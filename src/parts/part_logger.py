
import codecs
import json
import os
import selectors
import subprocess
import sys
import threading
import time
import traceback

import SCons.Script
from SCons.Debug import logInstanceCreation
from SCons.Environment import SubstitutionEnvironment as SConsEnvironment
from SCons.Errors import UserError

import parts.ansi_stream as ansi_stream
import parts.api as api
import parts.core.util as common
import parts.console as console
import parts.core.util as util
import parts.glb as glb
from parts.process_tools import killProcessTree, waitForProcess

# We need to close file descriptors on POSIX systems which have fork() mechanism right after
# the fork, otherwise all descriptors get inherited, and some files are being open much longer
# than we expect. We don't need this on Windows (or Cygwin) because on Windows processes don't
# inherit parent file descriptors by default, so nothing to close.
closeFileDescriptors = sys.platform not in ('win32', 'cygwin')

# On Windows select() only accepts sockets, so an anonymous pipe cannot be polled there and
# the reader has no way to wake itself up. POSIX gets the interruptible reader; Windows keeps
# a blocking readline() loop and depends on close()'s bounded join to stop a stuck reader
# from stalling the whole build.
canPollPipes = sys.platform not in ('win32', 'cygwin')

# poll() needs no descriptor of its own, where epoll and kqueue each allocate one. With two
# readers per concurrent task that saves 2*N descriptors on a wide build.
_selector_class = getattr(selectors, 'PollSelector', selectors.DefaultSelector)


def _env_seconds(name, default):
    '''Read a timeout override out of the environment, ignoring anything unusable.

    Read once, at import, so these have to be set in the environment scons is launched from
    rather than on its command line.
    '''
    try:
        value = float(os.environ[name])
    except (KeyError, TypeError, ValueError):
        return default
    return value if value > 0 else default


class pipeRedirector:

    # How long close() waits for the reader to finish before giving up on it. Expected to
    # matter only where the reader cannot be interrupted.
    join_timeout = _env_seconds('PARTS_LOG_JOIN_TIMEOUT', 30.0)
    # How long the reader keeps draining after being asked to stop. This has to be bounded: a
    # leftover process that keeps writing holds the pipe readable for as long as it lives, so
    # an unbounded drain would never honour the stop request at all. Only a lingering process
    # that is still producing output costs the full grace; a quiet one costs one poll_interval
    # and the ordinary case costs nothing, since the reader stops at EOF. part_spawner nests
    # two readers per task, so the worst case is twice this.
    drain_grace = _env_seconds('PARTS_LOG_DRAIN_GRACE', 2.0)
    # how often the interruptible reader wakes up to notice that close() asked it to stop
    poll_interval = 0.25
    read_size = 65536

    def _readerthread(self):
        try:
            if canPollPipes:
                self._read_interruptible()
            else:
                self._read_blocking()
        except Exception:
            # There was an error... that shouldn't happen, but still it did. So we report it
            # to the caller and then keep the pipe drained: if nothing reads it the spawned
            # program blocks forever once the pipe fills, and closing it instead kills the
            # program with EPIPE. Throwing away the rest of the text is the least bad option.
            self.error = traceback.format_exc()
            self._discard()
        finally:
            # The reader owns the pipe, not close(). close() cannot release it safely -- it may
            # have given up on a reader that is still inside a read -- so however this thread
            # ends, it hands the descriptor back on the way out. Otherwise every task whose
            # reader had to be abandoned leaks two descriptors for the life of the build.
            self._close_pipe()

    def _close_pipe(self):
        pipe, self.pipein = self.pipein, None
        if pipe is not None:
            try:
                pipe.close()
            except Exception:
                pass

    def _write(self, text):
        # An abandoned reader must stop logging. part_spawner calls TaskEnd as soon as close()
        # returns, and that drops the logger's cache entry for this task, so a later write
        # either raises KeyError or -- with a single job, where text goes straight out -- lands
        # in the middle of an unrelated task's console output. Draining continues so the
        # spawned program cannot block on a full pipe; only the logging stops.
        # (decoding also legitimately produces nothing when a read ends mid-character)
        if text and not self.detached:
            self.output.WriteStream(self.taskId, self.streamId, text)

    def _decoder(self):
        # Decode incrementally: a multi-byte character can be split across two reads, as the
        # write end of the pipe is inherited by the child's own children and writes larger
        # than PIPE_BUF are not atomic, so neither a line nor a read holds whole characters.
        # Undecodable bytes become U+FFFD instead of raising -- nothing downstream accepts
        # bytes, so letting a decode error escape would take down the build over log text.
        return codecs.getincrementaldecoder('utf-8')(errors='replace')

    def _read_interruptible(self):
        '''Read the pipe without ever blocking indefinitely, so close() can stop this thread
        by clearing self.executing.

        Breaking a blocking readline() by closing the pipe under it cannot work, which is
        worth recording because it looks like it should: BufferedReader.close() has to take
        the buffer lock, and the in-flight read holds that lock until it returns, so close()
        ends up waiting on precisely the read it was meant to interrupt.
        '''
        decoder = self._decoder()
        fd = self.pipein.fileno()
        os.set_blocking(fd, False)
        pending = bytearray()
        deadline = None
        with _selector_class() as selector:
            selector.register(fd, selectors.EVENT_READ)
            while True:
                if deadline is None and not self.executing:
                    # close() has asked us to stop. Keep draining for a moment so text already
                    # in the pipe still gets logged, but put a bound on it: a leftover process
                    # that keeps writing holds the pipe readable for as long as it lives, and
                    # an unbounded drain would ignore the stop request entirely, leaving
                    # close() to time out instead.
                    deadline = time.monotonic() + self.drain_grace
                if deadline is not None and time.monotonic() >= deadline:
                    break
                if not selector.select(timeout=self.poll_interval):
                    # Nothing readable. If we have been asked to stop, the pipe has gone quiet
                    # and there is nothing left to drain, so leave straight away.
                    if not self.executing:
                        break
                    continue
                try:
                    data = os.read(fd, self.read_size)
                except BlockingIOError:
                    continue
                if not data:
                    break                   # EOF: every writer has let go of the write end
                # pending never holds a newline, so only the new chunk has to be searched.
                # Re-searching the whole accumulated buffer on every read -- which splitting
                # one line at a time does -- is quadratic in the length of a newline-free
                # stream, and progress meters emit exactly that for long stretches.
                end = data.rfind(b'\n')
                if end < 0:
                    pending += data
                    continue
                head = bytes(pending) + data[:end + 1]
                pending = bytearray(data[end + 1:])
                start = 0
                while True:
                    nl = head.find(b'\n', start)
                    if nl < 0:
                        break
                    self._write(decoder.decode(head[start:nl + 1]))
                    start = nl + 1
        if pending:
            self._write(decoder.decode(bytes(pending)))  # a final line with no newline
        self._write(decoder.decode(b'', final=True))

    def _read_blocking(self):
        '''Windows reader. readline() cannot be interrupted, so a reader parked in here can
        only be abandoned by close().'''
        decoder = self._decoder()
        data = b' '
        while data:
            data = self.pipein.readline()
            self._write(decoder.decode(data))
        self._write(decoder.decode(b'', final=True))

    def _discard(self):
        '''Drain and throw away whatever is left in the pipe after a reader failure.'''
        try:
            fd = self.pipein.fileno()
            while self.executing:
                try:
                    if not os.read(fd, self.read_size):
                        return              # EOF
                except BlockingIOError:
                    time.sleep(self.poll_interval)
        except Exception:
            pass

    def __init__(self, pipein, output, taskId, streamId):
        if __debug__:
            logInstanceCreation(self, 'parts.part_logger.pipeRedirector')
        self.pipein = pipein
        self.output = output
        self.taskId = taskId
        self.streamId = streamId
        # daemon: where the reader cannot be interrupted it has to be abandoned, and a
        # non-daemon thread parked in readline() would then block interpreter shutdown,
        # turning a stalled task into a build that never exits.
        self.thread = threading.Thread(target=self._readerthread, args=(), daemon=True)
        self.executing = True
        self.error = ''
        # set once close() gives up on the reader; see _write
        self.detached = False

    def __enter__(self):
        self.thread.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        if self.error:
            # there was an error during the read... raise it
            raise UserError('Error while redirecting pipe: {0}'.format(self.error))

    def close(self):
        if self.thread is None:
            return                      # already closed; an explicit close then __exit__
        # Ask the reader to stop, then wait for it. The pipe is deliberately not touched here:
        # closing it cannot break a blocking read (see _read_interruptible), and if we end up
        # giving up on a reader that is still running it would not be safe to close underneath
        # it either. The reader releases the pipe itself as it exits.
        self.executing = False
        self.thread.join(timeout=self.join_timeout)
        if self.thread.is_alive():
            # Stop it logging before TaskEnd removes this task from the logger's cache. Set
            # before the warning so there is no window where it could still write.
            self.detached = True
            # Expected only where the reader cannot be interrupted; on POSIX the bounded drain
            # means reaching here implies the reader is stuck somewhere other than its poll
            # loop. Abandon it -- the thread is a daemon and will release the pipe if it ever
            # finishes. show_stack is off because the frame is this line and building it walks
            # unsynchronized global state (glb.part_frame) from a build worker thread; a build
            # that leaks one lingering process usually leaks many, hence print_once.
            api.output.warning_msg(
                'A log reader did not stop within {0} seconds and has been abandoned. Some '
                'command output may be missing from the part logs. A process spawned by the '
                'build is probably still holding its output pipe open.'.format(self.join_timeout),
                show_stack=False, print_once=True)
        self.thread = None


class part_spawner:
    __slots__ = ['env']

    def __init__(self, env=None):
        if __debug__:
            logInstanceCreation(self, 'parts.part_logger.part_spawner')
        self.env = env

    def __call__(self, shell, escape, cmd, args, Env):
        # setup the call
        ENV = {}
        for k, v in Env.items():
            if not isinstance(k, str):
                k = k.decode()
            if not isinstance(v, str):
                v = v.decode()
            ENV[k] = v

        # get the part_logger
        output = self.env._get_part_log_mapper()

        # we ignore the escape function as it breaks linux,
        # and was breaking on python 2.7 windows by adding extra " values
        # ie '"c:\program file\x.exe" foo bar"' -> '""c:\program file\x.exe" foo bar""'
        # we assume the command has "quotes" around it as need
        command_line = " ".join(args)

        # TempFileMunge issues handling. When executing command using TEMPFILE
        # the command-line is lost in per-component log files.
        # To overcome the issue TempFileMunge returns original command-line as
        # id property of second command argument. Use it for logging.
        try:
            command_id = args[1].id
        except (AttributeError, IndexError):
            command_id = command_line

        ret = -42  # The universal answer we return in case of exception
        # tell it we are starting a given action/command, get action_id
        id = output.TaskStart('{0}\nENV = {1}\n'.format(command_id, json.dumps(ENV)))
        try:
            # do the call
            proc = subprocess.Popen(
                command_line,
                shell=True,
                executable=shell,
                env=ENV,
                close_fds=closeFileDescriptors,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

            timeout = self.env.get('TIME_OUT', None)
            if timeout:
                # might be passed in on the command line, so it would be a string value
                timeout = float(timeout)

            # get the output and redirect to logger
            with pipeRedirector(proc.stdout, output, id, console.Console.out_stream):
                with pipeRedirector(proc.stderr, output, id, console.Console.error_stream):
                    waitForProcess(proc, timeout)
                    if proc.poll() is None:
                        killProcessTree(proc)
                        raise UserError("Killed by timeout ({0} sec)".format(timeout))
                    ret = proc.returncode
        except Exception as e:
            msg = str(SCons.Errors.convert_to_BuildError(e, sys.exc_info()))
            output.WriteStream(id, console.Console.error_stream, msg)
            ret = -1
            raise
        finally:
            # we are done, so tell logger this action is done.
            output.TaskEnd(id, ret)
        return ret


class part_logger:

    class StreamChunk:
        __slots__ = ['stream', 'msg', 'lock']

        def __init__(self, stream, msg):
            self.stream = stream
            self.msg = msg
            self.lock = threading.RLock()

    def __init__(self, env):
        self.env = env
        self.reporter = glb.rpter
        self.block_text = SCons.Script.GetOption('num_jobs') > 1
        self.cache = {}
        self.cacheLock = threading.RLock()

        log = env['PART_LOGGER']
        if util.isString(log):
            if log[0] != '$':
                log = "$" + log
            log = env.subst(log, raw=1, conv=lambda x: x)
            if util.isString(log):
                log = part_nil_logger
        self.other_out = log(env)
        self.streamWrite = {console.Console.out_stream: self.reporter.stdout,
                            console.Console.error_stream: self.reporter.stderr}
        self.otherOutWrite = {console.Console.out_stream: self.other_out.Out,
                              console.Console.error_stream: self.other_out.Err}

    def TaskStart(self, msg):
        taskId = hash(msg)
        with self.cacheLock:
            while taskId in self.cache:
                taskId += 1
            self.cache[taskId] = None
        self.other_out.Start(taskId, msg)
        return taskId

    def TaskEnd(self, taskId, exitCode):
        self._empty_cache(taskId)
        self.other_out.End(taskId, exitCode)
        try:
            with self.cacheLock:
                del self.cache[taskId]
        except KeyError:
            pass

    def WriteStream(self, taskId, stream, msg):
        if isinstance(msg, bytes):
            # Nothing below this point handles bytes: the chunk cache concatenates onto a
            # str, _empty_cache joins with str separators, and strip_ansi_codes compares
            # against str. Normalize here so no caller can poison those paths.
            msg = msg.decode('utf-8', errors='replace')
        if not self.block_text:
            self.streamWrite[stream](msg)
            self.otherOutWrite[stream](taskId, msg)
        else:
            with self.cacheLock:
                chunk = self.cache[taskId]
                if not chunk:
                    # uninitialized cache for this taskId, create it and we're done for now
                    self.cache[taskId] = self.StreamChunk(stream=stream, msg=msg)
                    return
            # now we have logging chunk... sync on its own lock
            with chunk.lock:
                if chunk.stream == stream:
                    # just appending to the currently chunked stream, nothing to do
                    chunk.msg += msg
                else:
                    # stream changed... flush old one and re-create the stream chunk
                    self._empty_cache(taskId)
                    chunk.stream = stream
                    chunk.msg = msg

    def _empty_cache(self, taskId):
        with self.cacheLock:
            chunk = self.cache[taskId]
        if not chunk:
            # there was no cache created, nothing to flush
            return

        with chunk.lock:
            stream, msg = chunk.stream, chunk.msg

        groupedStr = []
        for line in msg.splitlines():
            if not line:
                continue
            elif not groupedStr:
                groupedStr = [line]
            elif line[0] in (' ', '\t'):  # group indented text
                groupedStr.append(line)
            else:
                outLine = '\n'.join(groupedStr) + '\n'
                self.streamWrite[stream](outLine)
                self.otherOutWrite[stream](taskId, outLine)
                groupedStr = [line]
        outLine = '\n'.join(groupedStr) + '\n'
        self.streamWrite[stream](outLine)
        self.otherOutWrite[stream](taskId, outLine)


class part_nil_logger:
    ''' the point of this class is to define the base interface for all part logger
    items. The goal is the this object is to be a empty object that can be written to
    in case that no other item is provided, or if logging is turned off'''

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self, 'parts.part_logger.part_nil_logger')
        pass

    def Start(self, id, cmd):
        pass

    def End(self, id, exit_code):
        pass

    def Out(self, id, msg):
        pass

    def Err(self, id, msg):
        pass

    def TaskStart(self, msg):
        pass

    def TaskEnd(self, id, exit_code):
        pass


class log_file_writer:
    '''
    This context manager provides serialized access to log files.
    Usage:
        with log_file_writer("${my_log_file}", env) as output:
            output.write("Hello world!\n")

    The class ensures there is only one log writer instance per each
    log file.
    '''
    __slots__ = ('nodepath', 'file', 'lock')
    __lock__ = threading.Lock()

    def __new__(cls, name, env):
        with cls.__lock__:
            try:
                return env.File(name, create=0).attributes.log_file_writer
            except (UserError, AttributeError) as e:
                # UserError is raised by env.File when the file is unknown to SCons
                # AttributeError is raised when there is no log_file_writer_ref
                # among the file's attributes
                node = env.File(name)
                if isinstance(e, UserError):
                    # Scons knows nothing about the node. Need to clean up the file
                    node.prepare()  # Make sure the file path created
                    with open(node.abspath, 'w'):
                        pass
                node.attributes.log_file_writer = result = super(log_file_writer, cls).__new__(cls)
                result.nodepath = node.abspath
                result.lock = threading.Lock()
                if __debug__:
                    logInstanceCreation(result)
                return result

    def __enter__(self):
        self.lock.__enter__()
        self.file = open(self.nodepath, 'a+')
        return self.file.__enter__()

    def __exit__(self, exc_type, value, traceback):
        try:
            self.file.__exit__(exc_type, value, traceback)
        finally:
            self.lock.__exit__(exc_type, value, traceback)


if sys.platform == 'win32':
    try:  # Python 3.4+
        time_func = time.perf_counter
    except AttributeError:  # Earlier than Python 3.
        time_func = time.clock
else:
    time_func = time.time


class parts_text_logger:

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self, 'parts.part_logger.parts_text_logger')
        self.writer = log_file_writer('${LOG_PART_DIR}/${LOG_PART_FILE_NAME}', env)
        self.cache = {}
        self.times = {}

    def Start(self, id, cmd):
        self.times[id] = time_func()
        if not cmd.endswith('\n'):
            cmd += '\n'
        self.cache[id] = [
            (console.Console.out_stream, 'Task:' + cmd),
            (console.Console.out_stream,
             "Output begin ----------------------------------------------------------------\n")
        ]

    def End(self, id, exit_code):
        s = "".join(content for (text_type, content) in self.cache.pop(id, [])
                    if text_type in (console.Console.out_stream, console.Console.error_stream))
        s += "Output end   ----------------------------------------------------------------\n"
        s += "return code = " + str(exit_code) + "\n"
        s += "Elapsed time {0:.6f} seconds\n".format(time_func() - self.times.pop(id))
        s = ansi_stream.strip_ansi_codes(s)
        with self.writer as output:
            output.write(s)

    def Out(self, id, msg):
        self.cache[id].append((console.Console.out_stream, msg))

    def Err(self, id, msg):
        self.cache[id].append((console.Console.error_stream, msg))

    def __del__(self):
        try:
            cache = self.cache
            times = self.times
            writer = self.writer
        except AttributeError:
            return
        s = ""
        for id in list(cache.keys()):
            s += "".join(content for (text_type, content) in cache.pop(id)
                         if text_type in (console.Console.out_stream, console.Console.error_stream))
            s += "Build interupted] (return code = 1)\n"
            s += "Elapsed time {0:.6f} seconds\n".format(time_func() - times.pop(id))
        if s:
            s = ansi_stream.strip_ansi_codes(s)
            with writer as output:
                output.write(s)


def _get_part_log_mapper(env):
    try:
        result = env['PART_LOG_MAPPER']
    except KeyError:
        result = part_nil_logger(env)
    else:
        if util.isString(result):
            result = env.subst(result, raw=1, conv=lambda x: x)
    return result


api.register.add_method(_get_part_log_mapper)

api.register.add_variable('_part_logger', part_logger, '')
api.register.add_variable('PART_LOG_MAPPER', '${_part_logger(__env__)}', '')
api.register.add_variable('PART_SPAWNER', part_spawner, '')
api.register.add_variable('PART_LOGGER', 'PART_NIL_LOGGER', '')
api.register.add_variable('PART_NIL_LOGGER', part_nil_logger, '')
api.register.add_variable('PART_TEXT_LOGGER', parts_text_logger, '')
api.register.add_variable('LOG_PART_DIR', '${LOG_DIR}', '')
api.register.add_variable('LOG_PART_FILE_NAME', '${PART_NAME}_${PART_VERSION}.log', '')
