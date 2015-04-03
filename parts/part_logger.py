import time
import glb
import common
import core.util as util
import console
import api.output
import version
from process_tools import waitForProcess, killProcessTree
import json

import SCons.Script

import subprocess, sys, string
import thread, threading
import platform
import traceback

from SCons.Debug import logInstanceCreation
from SCons.Errors import UserError

pyver = version.version(platform.python_version())
# We need to close file descriptors on POSIX systems which have fork() mechanism right after
# the fork, otherwise all descriptors get inherited, and some files are being open much longer
# than we expect. We don't need this on Windows (or Cygwin) because on Windows processes don't
# inherit parent file descriptors by default, so nothing to close.
closeFileDescriptors = sys.platform not in ('win32', 'cygwin')

class pipeRedirector(object):
    def _readerthread(self):
        line = ' '
        try:
            while line:
                line = self.pipein.readline()
                if line:
                    self.output.WriteStream(self.taskId, self.streamId, line)
        except:
            # There was an error... that shouldn't happen, but still it did. So we report it
            # to the caller and close our pipe end so that spawned program won't block
            self.error = traceback.format_exc()
            self.pipein.close()
            self.pipein = None

    def __init__(self, pipein, output, taskId, streamId):
        if __debug__: logInstanceCreation(self, 'parts.part_logger.pipeRedirector')
        self.pipein = pipein
        self.output = output
        self.taskId = taskId
        self.streamId = streamId
        self.thread = threading.Thread(target=self._readerthread, args=())
        self.executing = True
        self.error = ''

    def __enter__(self):
        self.thread.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        if self.error:
            # there was an error during the read... raise it
            raise UserError('Error while redirecting pipe: {0}'.format(self.error))

    def close(self):
        self.executing = False
        self.thread.join()
        if self.pipein:
            self.pipein.close()
        self.thread = None

class part_spawner(object):
    __slots__ = ['__weakref__', 'env']
    def __init__(self, env = None):
        if __debug__: logInstanceCreation(self, 'parts.part_logger.part_spawner')
        self.env = env

    def __call__(self, shell, escape, cmd, args, Env):
        # setup the call
        ENV = {}
        for k,v in Env.iteritems():
            ENV[k] = str(v)
        # get the part_logger
        output = self.env._get_part_log_mapper()

        # we ignore the escape function as it breaks linux,
        # and was breaking on python 2.7 windows by adding extra " values
        # ie '"c:\program file\x.exe" foo bar"' -> '""c:\program file\x.exe" foo bar""'
        # we assume the command has "quotes" around it as need
        if pyver < '2.7' and sys.platform == 'win32':
            command_line = escape(string.join(args))
        else:
            command_line = string.join(args)

        # TempFileMunge issues handling. When executing command using TEMPFILE
        # the command-line is lost in per-component log files.
        # To overcome the issue TempFileMunge returns original command-line as
        # id property of second command argument. Use it for logging.
        try:
            command_id = args[1].id
        except (AttributeError, IndexError):
            command_id = command_line

        ret = -42 # The universal answer we return in case of exception
        #tell it we are starting a given action/command, get action_id
        id = output.TaskStart('{0}\nENV = {1}\n'.format(command_id, json.dumps(ENV)))
        try:
            # do the call
            proc = subprocess.Popen(
                command_line,
                shell = True,
                executable = shell,
                env = ENV,
                close_fds = closeFileDescriptors,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE)

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
        except BaseException, e:
            msg = str(SCons.Errors.convert_to_BuildError(e, sys.exc_info()))
            output.WriteStream(id, console.Console.error_stream, msg)
            ret = -1
            raise
        finally:
            # we are done, so tell logger this action is done.
            output.TaskEnd(id, ret)
        return ret

class part_logger(object):
    class StreamChunk(object):
        __slots__ = ['stream', 'msg', 'lock']
        def __init__(self, stream, msg):
            self.stream = stream
            self.msg = msg
            self.lock = threading.RLock()

    def __init__(self,env):
        if __debug__: logInstanceCreation(self, 'parts.part_logger.part_logger')
        self.env = env
        self.reporter = glb.rpter
        self.block_text = SCons.Script.GetOption('num_jobs') > 1
        self.cache = {}
        self.cacheLock = threading.RLock()

        log = env['PART_LOGGER']
        if util.isString(log):
            if log[0] != '$':
                log = "$" + log
            log = env.subst(log, raw = 1, conv = lambda x: x)
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
            elif line[0] in (' ', '\t'): # group indented text
                groupedStr.append(line)
            else:
                outLine = '\n'.join(groupedStr) + '\n'
                self.streamWrite[stream](outLine)
                self.otherOutWrite[stream](taskId, outLine)
                groupedStr = [line]
        outLine = '\n'.join(groupedStr) + '\n'
        self.streamWrite[stream](outLine)
        self.otherOutWrite[stream](taskId, outLine)

class part_nil_logger(object):
    ''' the point of this class is to define the base interface for all part logger
    items. The goal is the this object is to be a empty object that can be written to
    in case that no other item is provided, or if logging is turned off'''
    def __init__(self, env):
        if __debug__: logInstanceCreation(self, 'parts.part_logger.part_nil_logger')
        pass
    def Start(self,id,cmd):
        pass
    def End(self,id,exit_code):
        pass
    def Out(self,id,msg):
        pass
    def Err(self,id,msg):
        pass
    def TaskStart(self,msg):
        pass
    def TaskEnd(self,id,exit_code):
        pass

class log_file_writer(object):
    '''
    This context manager provides serialized access to log files.
    Usage:
        with log_file_writer("${my_log_file}", env) as output:
            output.write("Hello world!\n")

    The class ensures there is only one log writer instance per each
    log file.
    '''
    __slots__ = ('nodepath', 'file', 'lock', '__weakref__')
    __lock__ = thread.allocate_lock()
    def __new__(cls, name, env):
        with cls.__lock__:
            try:
                return env.File(name, create = 0).attributes.log_file_writer
            except (UserError, AttributeError), e:
                # UserError is raised by env.File when the file is unknown to SCons
                # AttributeError is raised when there is no log_file_writer_ref
                # among the file's attributes
                node = env.File(name)
                if isinstance(e, UserError):
                    # Scons knows nothing about the node. Need to clean up the file
                    node.prepare() # Make sure the file path created
                    with open(node.abspath, 'w'):
                        pass
                node.attributes.log_file_writer = result = super(log_file_writer, cls).__new__(cls)
                result.nodepath = node.abspath
                result.lock = thread.allocate_lock()
                if __debug__: logInstanceCreation(result)
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
    time_func = time.clock
else:
    time_func = time.time

class parts_text_logger(object):
    def __init__(self, env):
        if __debug__: logInstanceCreation(self, 'parts.part_logger.parts_text_logger')
        self.writer = log_file_writer('${LOG_PART_DIR}/${LOG_PART_FILE_NAME}', env)
        self.cache = {}
        self.times = {}

    def Start(self, id, cmd):
        self.times[id] = time_func()
        if not cmd.endswith('\n'):
            cmd += '\n'
        self.cache[id] = [
            (console.Console.out_stream,'Task:' + cmd),
            (console.Console.out_stream,
            "Output begin ----------------------------------------------------------------\n")
            ]

    def End(self, id, exit_code):
        s  = "".join(content for (text_type, content) in self.cache.pop(id, [])
            if text_type in (console.Console.out_stream, console.Console.error_stream))
        s += "Output end   ----------------------------------------------------------------\n"
        s += "return code = " + str(exit_code) + "\n"
        s += "Elapsed time {0:.6f} seconds\n".format(time_func() - self.times.pop(id))
        with self.writer as output:
            output.write(s)

    def Out(self, id, msg):
        self.cache[id].append((console.Console.out_stream,msg))

    def Err(self, id, msg):
        self.cache[id].append((console.Console.error_stream,msg))

    def __del__(self):
        try:
            cache = self.cache
            times = self.times
            writer = self.writer
        except AttributeError:
            return
        s = ""
        for id in cache.keys():
            s += "".join(content for (text_type, content) in cache.pop(id)
                if text_type in (console.Console.out_stream, console.Console.error_stream))
            s += "Build interupted] (return code = 1)\n"
            s += "Elapsed time {0:.6f} seconds\n".format(time_func() - times.pop(id))
        with writer as output:
            output.write(s)

def _get_part_log_mapper(env):
    try:
        result = env['PART_LOG_MAPPER']
    except KeyError:
        result = part_nil_logger(env)
    else:
        if util.isString(result):
            result = env.subst(result, raw = 1, conv = lambda x: x)
    return result
from SCons.Environment import SubstitutionEnvironment as SConsEnvironment
SConsEnvironment._get_part_log_mapper = _get_part_log_mapper

api.register.add_variable('_part_logger',part_logger, '')
api.register.add_variable('PART_LOG_MAPPER', '${_part_logger(__env__)}','')
api.register.add_variable('PART_SPAWNER',part_spawner,'')
api.register.add_variable('PART_LOGGER','PART_NIL_LOGGER','')
api.register.add_variable('PART_NIL_LOGGER',part_nil_logger,'')
api.register.add_variable('PART_TEXT_LOGGER',parts_text_logger,'')
api.register.add_variable('LOG_PART_DIR','${LOG_DIR}','')
api.register.add_variable('LOG_PART_FILE_NAME','${PART_NAME}_${PART_VERSION}.log','')
