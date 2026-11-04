

import ctypes
import os
import sys
import re
import time
import _thread

import parts.color as color
from SCons.Debug import logInstanceCreation

win32 = sys.platform == 'win32'

# set once any stream has been reported dead, so the notice is printed once
_reported_dead_stream = False

# Control/Color Sequence
g_ansi_color_seq = re.compile('\001?\033\\[((?:\\d|;)*)([a-zA-Z])\002?')
# Operating System Command .. should not hit much of these at the moment
g_ansi_osc = re.compile('\001?\033\\]([^\a]*)(\a)\002?')

def strip_ansi_codes(in_str:str) -> str:
    '''
    This function is to remove ansi code from the string to make it
    easy to print text to console or log files.
    '''

    out = ''
    tmp_str = ''
    state = 0
    code = 0
    for s in in_str:
        if s == '\033':
            state = 1
            out+=tmp_str
            tmp_str = ''
        elif s == '[' and state == 1:
            state = 2
        elif state == 2:
            if s == ';' or s == 'm':
                code = 0
            else:
                try:
                    code = code * 10 + int(s)
                except ValueError:

                    code = 0
                    state = 0
            if s == 'm':

                state = 0
                code = 0
        else:
            tmp_str += s
    if tmp_str != '':
        out+=tmp_str
    return out

class ColorTextStream:
    '''Basically is an object that wraps a stream and process color ansi
    command codes for color
    '''

    # How long safe_write() will wait on a non-blocking stream that is accepting
    # nothing before it drops the text. It waits with the console lock held, so
    # this bounds how long one stalled stream can hold up every thread that logs.
    STALL_TIMEOUT = 1.0
    # Once that budget is spent, how long to drop cheaply before allowing another
    # bounded wait. Without this a stream that stalled once would never be waited
    # on again; with it, a reader that comes back is picked up within this long.
    STALL_RETRY_AFTER = 5.0

    def __init__(self, console, stream):
        if __debug__:
            logInstanceCreation(self)
        self.__console = console
        # the stream object
        self.__stream = stream
        # default colors for this stream
        self.__color = color.ConsoleColor()
        self.__reset_color = color.ConsoleColor(color.SystemColor)
        self.__process_color = False
        self.__force_flush = False
        self.__clear_line = True
        # set once the stream stops accepting output for good, see safe_write().
        # Per instance on purpose: console.Out and console.Error wrap different
        # streams, so a dead stdout must not silence stderr.
        self.__dead = False
        # deadline for how long we are still willing to wait on a stream that is
        # accepting nothing. Per instance, not per call: a fresh budget for every
        # message would cost STALL_TIMEOUT per message with the console lock
        # held, which is the wedge this is meant to prevent. Cleared whenever the
        # stream accepts something, so a reader that merely paused gets full
        # patience again.
        self.__stall_deadline = None

    def _set_color(self, val):
        self.__color = val

    def _get_color(self):
        return self.__color
    # control what color is used
    Color = property(_get_color, _set_color)

    def _set_process_color(self, val):
        self.__process_color = val

    def _get_process_color(self):
        # test if we have a bad color
        # if self.__color.Background() == color.Default and self.__color.Foreground() == color.Default:
        #    return False
        return self.__process_color
    # controls if the color should be processed
    ProcessColor = property(_get_process_color, _set_process_color)

    def _set_force_flush(self, val):
        self.__force_flush = val

    def _get_force_flush(self):
        return self.__force_flush
    # controls if after a write we force a flush
    ForceFlush = property(_get_force_flush, _set_force_flush)

    def _set_clear_line(self, val):
        self.__clear_line = val

    def _get_clear_line(self):
        return self.__clear_line
    # controls if clear the whole console line before we write
    # needed when switching between stream that write to a stream
    # vs a raw console
    ClearLine = property(_get_clear_line, _set_clear_line)

    def write(self, s, lock=True):
        if lock:
            self.__console.lock()
        if self.__console.clearline and self.__clear_line:
            self.__console.clearline = False
            self.__console.ClearLine()
        try:
            if self.ProcessColor:
                self._WriteColor(self.__color.ansi_value() + s + self.__reset_color.ansi_value())
            else:
                self._WriteNoColor(s)
        finally:
            if lock:
                self.__console.release()

    def flush(self, lock=True):
        if self.__dead:
            return
        if lock:
            self.__console.lock()
        try:
            while True:
                try:
                    self.__stream.flush()
                except InterruptedError:
                    # A signal interrupted the flush, so it did not happen.
                    # Returning here would tell the caller the stream was
                    # flushed when the final buffered output is still sitting
                    # there, so retry under the same bound the write path uses.
                    if not self.__wait_for_drain():
                        return
                    continue
                except BlockingIOError:
                    # Different case: the data is buffered and a later flush can
                    # push it. Nothing is lost by deferring, and retrying a full
                    # buffer here would just burn the stall budget.
                    return
                except (OSError, ValueError):
                    # same reasoning as safe_write(): a build must not fail
                    # because the far end of its output went away.
                    # Console.flush() delegates straight here, so without this a
                    # closed pipe propagates BrokenPipeError out of an ordinary
                    # logging call.
                    self.__mark_dead()
                    return
                else:
                    self.__stall_deadline = None
                    return
        finally:
            if lock:
                self.__console.release()

    def writeLines(self, str_list, lock=True):

        if lock:
            self.__console.acquire()
        if self.__console.clearline and self.__clear_line:
            self.__console.clearline = False
            self.__console.ClearLine()
        try:
            if self.ProcessColor:
                self._WriteColor(self.__color.ansi_value())
                for s in str_list:
                    self._WriteNoColor(s)
                self._WriteColor(self.__reset_color.ansi_value())
            else:
                for s in str_list:
                    self._WriteNoColor(s)
        finally:
            if lock:
                self.__console.release()

    if win32:
        def SetColor(self, console_color):
            handle = ctypes.windll.kernel32.GetStdHandle(-11)
            ctypes.windll.kernel32.SetConsoleTextAttribute(handle, console_color.SystemValue())

    def _WriteColor(self, in_str):
        if win32:
            tmp_str = ''
            state = 0
            code = 0
            col = color.ConsoleColor(color.default_color.Foreground(), color.default_color.Background())
            code_type = None
            fg_bold = None
            bk_bold = None
            for s in in_str:
                if s == '\033':
                    state = 1
                    if tmp_str != '':
                        self.safe_write(tmp_str)
                        tmp_str = ''
                elif s == '[' and state == 1:
                    state = 2
                elif state == 2:
                    if s == ';' or s == 'm':
                        # process code
                        if code >= 30 and code < 38:
                            col.Foreground(code - 30)
                        elif code >= 90 and code < 98:
                            col.Foreground(code - 82)
                            fg_bold = True
                        elif code >= 40 and code < 48:
                            col.Background(code - 40)
                        elif code >= 100 and code < 108:
                            col.Background(code - 92)
                            bk_bold = True
                        elif code == 1:
                            fg_bold = True
                        elif code == 2:
                            fg_bold = False

                        elif code == 0:
                            # reset
                            col.Background(color.default_color.Background())
                            col.Foreground(color.default_color.Foreground())
                            fg_bold = None
                            bk_bold = None
                        code = 0
                    elif s == 'K' and code_type is None:
                        tmp = (self.__console.Width - self.__console.Cursor.X) - 1
                        if tmp > 0:
                            tmp_str += " " * tmp
                        state = 0
                        code = 0
                    else:
                        try:
                            code = code * 10 + int(s)
                            code_type = 'color'
                        except ValueError:
                            code = 0
                            state = 0
                            code_type = None

                    if s == 'm':
                        if fg_bold == True:
                            tmp = col.Foreground()
                            if tmp < 8:
                                col.Foreground(tmp + 8)
                        elif fg_bold == False:
                            tmp = col.Foreground()
                            if tmp > 7:
                                col.Foreground(tmp - 8)
                        if bk_bold == True:
                            tmp = col.Background()
                            if tmp < 8:
                                col.Background(tmp + 8)
                        self.SetColor(col)
                        state = 0
                        code = 0
                        code_type = None
                else:
                    tmp_str += s
            if tmp_str != '':
                self.safe_write(tmp_str)
        else:
            self.safe_write(in_str)

    def _WriteNoColor(self, in_str):
        '''Will just strip the codes'''

        tmp_str = ''
        state = 0
        code = 0
        for s in in_str:
            if s == '\033':
                state = 1
                self.safe_write(tmp_str)
                tmp_str = ''
            elif s == '[' and state == 1:
                state = 2
            elif state == 2:
                if s == ';' or s == 'm':
                    code = 0
                else:
                    try:
                        code = code * 10 + int(s)
                    except ValueError:

                        code = 0
                        state = 0
                if s == 'm':

                    state = 0
                    code = 0
            else:
                tmp_str += s
        if tmp_str != '':
            self.safe_write(tmp_str)

    def safe_write(self, data_str):
        # Nothing this stream will ever accept again, so do not spend a syscall
        # per line for the rest of the build finding that out.
        if self.__dead:
            return

        written = 0
        while written < len(data_str):
            try:
                count = self.__stream.write(data_str[written:])
            except (BlockingIOError, InterruptedError):
                # BlockingIOError: a non-blocking stream is full and wants to be
                # retried. InterruptedError: a signal arrived mid-write, which
                # leaves the descriptor perfectly usable (and which python
                # normally retries internally, PEP 475). Neither is a reason to
                # write the stream off.
                #
                # The same slice is offered again rather than advancing by
                # BlockingIOError.characters_written. Despite the name that is a
                # *byte* count, not a character count: the exception comes from
                # the buffered I/O layer, which only ever deals in bytes. CPython
                # documented it as bytes rather than changing it, see
                # python/cpython#83926. Using it to index a str would corrupt any
                # non-ASCII output, and even converting it through the stream's
                # encoding does not help, because the accepted byte prefix can
                # end in the middle of a multi-byte character, so there is no
                # character index to resume from. Re-offering can therefore
                # duplicate what the stream already took, which is the lesser
                # evil, and is what this code did before the retry was bounded.
                if not self.__wait_for_drain():
                    # Give up on the rest of this message, but break rather than
                    # return: whatever the buffered layer already took still
                    # deserves the force-flush below.
                    break
                continue
            except (OSError, ValueError):
                # OSError covers EPIPE, EBADF and EIO: the far end is gone and
                # every retry fails the same way. ValueError is what a closed
                # stream raises ("I/O operation on closed file"), which is just
                # as final and is not an OSError. Retrying either is what turned
                # "scons ... | head" into an unkillable busy loop holding the
                # console lock. Give up on the stream instead; losing log text
                # beats wedging the build.
                self.__mark_dead()
                return

            # python2 returned None, python3 returns the count written
            if count is None:
                # python2 shape: assume it took everything, which counts as the
                # stream moving.
                self.__stall_deadline = None
                break
            if count == 0:
                # It accepted nothing and did not say why, so it will not take
                # the rest either. Deliberately does NOT clear the deadline: a
                # stream alternating between zero and EAGAIN would otherwise buy
                # a fresh STALL_TIMEOUT every round and rebuild the very delays
                # the per-instance budget exists to stop.
                break
            # The stream is moving, so restore full patience for the next stall.
            self.__stall_deadline = None
            written += count

        if self.__force_flush:
            # After the loop rather than inside it. The loop exits by several
            # paths and text still has to be pushed out on all of them; doing it
            # per chunk also flushed more often than necessary.
            self.flush(lock=False)

    def __wait_for_drain(self):
        '''Bounded wait for a stream that is not accepting anything.

        Returns True to retry, False to give up on this write. The budget lives
        on the instance and refreshes only when the stream accepts something, so
        a stream that never drains costs one write attempt per message rather
        than STALL_TIMEOUT per message with the console lock held.
        '''
        now = time.monotonic()
        deadline = self.__stall_deadline
        if deadline is None:
            self.__stall_deadline = now + self.STALL_TIMEOUT
        elif now >= deadline:
            if now - deadline < self.STALL_RETRY_AFTER:
                # Still in the cooldown. Deliberately leaves the deadline in the
                # past: a fresh budget per message would make a permanently
                # stalled stream a wedge again, just a slower one.
                return False
            # Long enough since we gave up that the reader may be back.
            self.__stall_deadline = now + self.STALL_TIMEOUT
        # Wait for the reader rather than spinning on a full buffer.
        time.sleep(0.001)
        return True

    def __mark_dead(self):
        global _reported_dead_stream
        self.__dead = True
        # Console.Output, .Message, .Trace and .Verbose are separate instances
        # over the same sys.__stdout__, so a closed stdout gets here once per
        # instance. Say it once.
        if _reported_dead_stream:
            return
        # The dead stream cannot carry news of its own death, and reporting this
        # through api.output would come straight back here. Go to the real
        # stderr, which is usually still open: it is a different file
        # descriptor, and only one end of a pipeline tends to close.
        try:
            if sys.__stderr__ is not None and sys.__stderr__ is not self.__stream:
                sys.__stderr__.write(
                    "Parts: an output stream closed early; further output to it is dropped\n")
                # Latched only once it is actually out. Setting it earlier meant a
                # first death that could not print the notice silenced it for
                # every later one.
                _reported_dead_stream = True
        except Exception:
            # Last-resort notice. If even this fails there is nowhere left to
            # complain to, and raising would lose the build error we were most
            # likely in the middle of reporting.
            pass
