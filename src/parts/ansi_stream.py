from __future__ import absolute_import, division, print_function

import ctypes
import os
import sys

import parts.color as color
from SCons.Debug import logInstanceCreation

win32 = sys.platform == 'win32'

import _thread

class ColorTextStream(object):
    '''Basically is an object that wraps a stream and process color ansi
    command codes for color
    '''

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
        if lock:
            self.__console.lock()
        try:
            self.__stream.flush()
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
        # self.stream.write(in_str)
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
            #in_str = "Thread->{0}\n{1}\nThreadend->{0}\n".format(_thread.get_ident(),in_str)
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
        written = 0
        #data_str=data_str.encode()
        while written < len(data_str):
            try:
                #written = written + os.write(self.__stream.fileno(), data_str[written:])
                written = written + self.__stream.write(data_str[written:])
                if self.__force_flush:
                    self.__stream.flush()
            except OSError as e:
                pass
