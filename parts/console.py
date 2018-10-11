import ansi_stream
import color
import sys
import thread

import struct
import ctypes
# for non windows
if not color.is_win32:
    import fcntl
    import termios

from SCons.Debug import logInstanceCreation

import SCons.Script
SCons.Script.AddOption("--console-stream",
                       dest='console-stream',
                       default='tty',
                       nargs=1,
                       type='choice',
                       choices=['none', 'tty', 'stdout', 'stderr'],
                       action='store',
                       help='Control how Parts maps the console stream. Values can be none, tty, con:, stdout, stderr')

# refactor these calls to a different file to avoid C&P
opt_true_values = set(['y', 'yes', 'true', 't', '1', 'on', 'all'])
opt_false_values = set(['n', 'no', 'false', 'f', '0', 'off', 'none'])


def opt_bool(option, opt, value, parser, var):
    if value is None:
        setattr(parser.values, var, True)
        return
    tmp = value.lower()
    if tmp in opt_true_values:
        setattr(parser.values, var, True)
    elif tmp in opt_false_values:
        setattr(parser.values, var, False)
    else:
        raise OptionValueError('Invalid value for boolean option "%s" value "%s"\n Valid options are %s' %
                               (var.replace('-', '_'), value, opt_true_values | opt_false_values))


SCons.Script.AddOption("--show-progress",
                       dest='show_progress',
                       nargs='?',
                       callback=lambda option, opt, value, parser: opt_bool(option, opt, value, parser, 'show_progress'),
                       type='string',
                       action='callback',
                       help='Controls if progress state is shown')

SCons.Script.AddOption("--hide-progress",
                       dest='show_progress',
                       default=True,
                       action="store_false",
                       help='Controls if progress state is shown')


class NullStream(object):

    def __init__(self):
        if __debug__:
            logInstanceCreation(self)
        pass

    def close(self):
        pass

    def write(self, s):
        pass

    def writeLines(self, str_list):
        pass

    def flush(self):
        pass


class Cursor(object):

    def __init__(self, *args):
        if __debug__:
            logInstanceCreation(self)
        try:
            self.__x, self.__y = args
        except ValueError:
            coord = args[0]
            self.__x, self.__y = coord.X, coord.Y

    @property
    def X(self):
        return self.__x

    @property
    def Y(self):
        return self.__y


if color.is_win32:
    import ctypes.wintypes
    # From WinBase.h
    STD_INPUT_HANDLE = ctypes.wintypes.DWORD(-10)
    STD_OUTPUT_HANDLE = ctypes.wintypes.DWORD(-11)
    STD_ERROR_HANDLE = ctypes.wintypes.DWORD(-12)

    GetStdHandle = ctypes.windll.kernel32.GetStdHandle
    GetStdHandle.restype = ctypes.wintypes.HANDLE
    GetStdHandle.argtypes = (ctypes.wintypes.DWORD,)

    class CONSOLE_SCREEN_BUFFERINFO(ctypes.Structure):
        _fields_ = (
            ("dwSize", ctypes.wintypes._COORD),
            ("dwCursorPosition", ctypes.wintypes._COORD),
            ("wAttributes", ctypes.wintypes.WORD),
            ("srWindow", ctypes.wintypes.SMALL_RECT),
            ("dwMaximumWindowSize", ctypes.wintypes._COORD),
        )
    LPCONSOLE_SCREEN_BUFFERINFO = ctypes.POINTER(CONSOLE_SCREEN_BUFFERINFO)
    assert ctypes.sizeof(CONSOLE_SCREEN_BUFFERINFO()) == 22
    GetConsoleScreenBufferInfo = ctypes.windll.kernel32.GetConsoleScreenBufferInfo
    GetConsoleScreenBufferInfo.restype = ctypes.wintypes.BOOL
    GetConsoleScreenBufferInfo.argtypes = (
        ctypes.wintypes.HANDLE,      # hConsoleOutput
        LPCONSOLE_SCREEN_BUFFERINFO,  # lpConsoleScreenBufferInfo
    )


class Console(object):
    ''' only support output operations at this time'''
    out_stream = 1
    error_stream = 2
    warning_stream = 3
    message_stream = 4
    trace_stream = 5
    verbose_stream = 6

    def __init__(self):
        if __debug__:
            logInstanceCreation(self)

        self.clearline = False
        self.__lock = thread.allocate_lock()  # used to sync output cases across streams
        try:
            map_console = SCons.Script.GetOption('console-stream')
            if map_console in ['tty', 'con:']:
                if color.is_win32:
                    conio = open('con:', 'w')
                else:
                    conio = open('/dev/tty', 'w')
            elif map_console in ['stdout']:
                conio = sys.__stdout__
            elif map_console in ['stderr']:
                conio = sys.__stderr__
            else:
                conio = NullStream()

            if SCons.Script.GetOption('show_progress') == False:
                conio = NullStream()
        except Exception as ec:
            conio = NullStream()

        # if color.is_win32==True:
         #   if color.default_color==color.ConsoleColor(0,0):
        self.__process_color = False

        self.__console = ansi_stream.ColorTextStream(
            self,
            conio,
        )
        self.__console.ClearLine = False
        self.Output = ansi_stream.ColorTextStream(
            self,
            sys.__stdout__
        )
        self.Error = ansi_stream.ColorTextStream(
            self,
            sys.__stderr__
        )
        self.Warning = ansi_stream.ColorTextStream(
            self,
            sys.__stderr__
        )
        self.Message = ansi_stream.ColorTextStream(
            self,
            sys.__stdout__
        )
        self.Trace = ansi_stream.ColorTextStream(
            self,
            sys.__stdout__
        )

        self.Verbose = ansi_stream.ColorTextStream(
            self,
            sys.__stdout__
        )

        # this items we want to force flush
        self.__console.ForceFlush = True
        self.Output.ForceFlush = True
        self.Message.ForceFlush = True
        self.Trace.ForceFlush = True
        self.Verbose.ForceFlush = True
        # these items we want an option to control if we force
        self.Error.ForceFlush = True
        self.Output.ForceFlush = True
        self.Warning.ForceFlush = True

    def ShutDown(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def _set_color(self, val):
        self.__console.Color = val

    def _get_color(self):
        return self.__console.Color
    # control what color is used
    Color = property(_get_color, _set_color)

    def _set_process_color(self, val):
        self.__process_color = val
        self.__console.ProcessColor = self.__process_color
        self.Output.ProcessColor = self.__process_color
        self.Error.ProcessColor = self.__process_color
        self.Warning.ProcessColor = self.__process_color
        self.Message.ProcessColor = self.__process_color
        self.Trace.ProcessColor = self.__process_color
        self.Verbose.ProcessColor = self.__process_color

    def _get_process_color(self):
        return self.__process_color
    # controls if the color should be processed
    ProcessColor = property(_get_process_color, _set_process_color)

    def write(self, msg):
        # write data
        self.__console.write(msg)
        self.clearline = True

    def flush(self):
        # write data
        self.__console.flush()

    if color.is_win32:
        @property
        def Width(self):
            # move to common var prevent repeating the getting of common value
            handle = ctypes.windll.kernel32.GetStdHandle(STD_ERROR_HANDLE)
            screen_buffer = CONSOLE_SCREEN_BUFFERINFO()
            if ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(screen_buffer)):
                return screen_buffer.srWindow.Right - screen_buffer.srWindow.Left + 1
            return 80

        @property
        def Height(self):
            # move to common var prevent repeating the getting of common value
            handle = ctypes.windll.kernel32.GetStdHandle(STD_ERROR_HANDLE)
            screen_buffer = CONSOLE_SCREEN_BUFFERINFO()
            if ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(screen_buffer)):
                return screen_buffer.srWindow.Bottom - screen_buffer.srWindow.Top + 1
            return 40

        @property
        def Cursor(self):
            # move to common var prevent repeating the getting of common value
            handle = ctypes.windll.kernel32.GetStdHandle(STD_ERROR_HANDLE)
            screen_buffer = CONSOLE_SCREEN_BUFFERINFO()
            if ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(screen_buffer)):
                return Cursor(screen_buffer.dwCursorPosition)
            return Cursor(0, 0)

    else:
        @property
        def Width(self):
            width = 0
            try:
                tmp = struct.pack('HHHH', 0, 0, 0, 0)
                data = fcntl.ioctl(1, termios.TIOCGWINSZ, tmp)
                width = struct.unpack('HHHH', data)[1]
            except IOError:
                pass
            # something went wrong
            if width <= 0:
                width = 80

            return width

        @property
        def Height(self):
            height = 0
            try:
                tmp = struct.pack('HHHH', 0, 0, 0, 0)
                data = fcntl.ioctl(1, termios.TIOCGWINSZ, tmp)
                height = struct.unpack('HHHH', data)[0]
            except IOError:
                pass
            # something went wrong
            if height <= 0:
                height = 40

            return height

    def ClearLine(self):
        s = "\r" + (" " * (self.Width - 1)) + "\r"
        self.__console.write(s, lock=not self.__lock.locked)

    def lock(self):
        self.__lock.acquire()

    def release(self):
        self.__lock.release()
