from __future__ import absolute_import, division, print_function

import sys
from optparse import OptionValueError

from SCons.Debug import logInstanceCreation

Dim = -4
Bold = -3
Bright = -3
SystemColor = -2
Default = -1
Black = 0x00
Red = 0x01
Green = 0x02
Yellow = 0x03
Blue = 0x04
Purple = 0x05
Magenta = 0x05
Aqua = 0x06
Cyan = 0x06
White = 0x07
Gray = 0x08
BrightRed = 0x09
BrightGreen = 0x0A
BrightYellow = 0x0B
BrightBlue = 0x0C
BrightPurple = 0x0D
BrightMagenta = 0x0D
BrightAqua = 0x0E
BrightCyan = 0x0E
BrightWhite = 0x0F


def color_to_str(color):
    if color == Dim:
        return "Dim"
    if color == Bold:
        return "Bold"
    if color == Bright:
        return "Bright"
    if color == SystemColor:
        return "SystemColor"
    if color == Default:
        return "Default"
    if color == Black:
        return "Black"
    if color == Red:
        return "Red"
    if color == Green:
        return "Green"
    if color == Yellow:
        return "Yellow"
    if color == Blue:
        return "Blue"
    if color == Purple:
        return "Purple/Magenta"
    if color == Aqua:
        return "Aqua/Cyan"
    if color == White:
        return "White"
    if color == Gray:
        return "Gray"
    if color == BrightRed:
        return "BrightRed"
    if color == BrightGreen:
        return "BrightGreen"
    if color == BrightYellow:
        return "BrightYellow"
    if color == BrightBlue:
        return "BrightBlue"
    if color == BrightPurple:
        return "BrightPurple/BrightMagenta"
    if color == BrightAqua:
        return "BrightAqua/BrightCyan"
    if color == BrightWhite:
        return "BrightWhite"
    return "Unknown Color"


class ConsoleColor(object):

    def __init__(self, fg_color=Default, bk_color=Default):
        if __debug__:
            logInstanceCreation(self)

        self.fg_color = fg_color

        # Can't set the background bold.. so we make this Default
        if bk_color == Bold:
            self.bk_color = Default
        else:
            self.bk_color = bk_color

    def Background(self, color=None):
        if color is None:
            return self.bk_color
        else:
            self.bk_color = color

    def Foreground(self, color=None):
        if color is None:
            return self.fg_color
        else:
            self.fg_color = color
    if sys.platform == 'win32':
        def map_color(self, col):
            if col == Red:
                col = Blue
            elif col == Blue:
                col = Red
            elif col == Yellow:
                col = Aqua
            elif col == Aqua:
                col = Yellow
            elif col == BrightRed:
                col = BrightBlue
            elif col == BrightBlue:
                col = BrightRed
            elif col == BrightYellow:
                col = BrightAqua
            elif col == BrightAqua:
                col = BrightYellow
            return col

        def SystemValue(self):

            if self.fg_color == SystemColor or self.fg_color == Default:
                fg_color = default_color.Foreground()
            elif self.fg_color == Bold and default_color.Foreground() < 8:
                fg_color = default_color.Foreground() + 8
            elif self.fg_color == Dim and default_color.Foreground() > 7:
                sys.__stdout__.write(str(default_color.Foreground()) + "\n")
                fg_color = default_color.Foreground() - 8
            else:
                fg_color = self.fg_color
            if self.bk_color == SystemColor or self.bk_color == Default:
                bk_color = default_color.Background()
            else:
                bk_color = self.bk_color
            return self.map_color(fg_color) + (self.map_color(bk_color) << 4)

    def __eq__(self, rhs):
        return self.bk_color == rhs.bk_color and self.fg_color == rhs.fg_color

    def __str__(self):
        return self.ansi_value()

    def __add__(self, rhs):
        return self.ansi_value() + rhs

    def __radd__(self, lhs):
        return lhs + self.ansi_value()

    def ansi_value(self):

        ret = ""
        if self.fg_color != Default or self.bk_color != Default:
            if self.fg_color == Bold:
                ret = "\033[1"
            elif self.fg_color == Dim:
                ret = "\033[2"
            elif self.fg_color == Black:
                ret = "\033[30"
            elif self.fg_color == Red:
                ret = "\033[31"
            elif self.fg_color == Green:
                ret = "\033[32"
            elif self.fg_color == Yellow:
                ret = "\033[33"
            elif self.fg_color == Blue:
                ret = "\033[34"
            elif self.fg_color == Purple:
                ret = "\033[35"
            elif self.fg_color == Aqua:
                ret = "\033[36"
            elif self.fg_color == White:
                ret = "\033[37"
            elif self.fg_color == Gray:
                ret = "\033[1;30"
            elif self.fg_color == BrightRed:
                ret = "\033[1;31"
            elif self.fg_color == BrightGreen:
                ret = "\033[1;32"
            elif self.fg_color == BrightYellow:
                ret = "\033[1;33"
            elif self.fg_color == BrightBlue:
                ret = "\033[1;34"
            elif self.fg_color == BrightPurple:
                ret = "\033[1;35"
            elif self.fg_color == BrightAqua:
                ret = "\033[1;36"
            elif self.fg_color == BrightWhite:
                ret = "\033[1;37"
            elif self.bk_color != Default and self.bk_color != SystemColor:
                ret = "\033["

            if (self.fg_color != Default and self.bk_color != Default) and\
                    (self.fg_color != SystemColor and self.bk_color != SystemColor):
                ret += ";"

            if self.bk_color == Black:
                ret += "40m"
            elif self.bk_color == Red:
                ret += "41m"
            elif self.bk_color == Green:
                ret += "42m"
            elif self.bk_color == Yellow:
                ret += "43m"
            elif self.bk_color == Blue:
                ret += "44m"
            elif self.bk_color == Purple:
                ret += "45m"
            elif self.bk_color == Aqua:
                ret += "46m"
            elif self.bk_color == White:
                ret += "47m"
            elif self.bk_color == Gray:
                ret += "100m"
            elif self.bk_color == BrightRed:
                ret += "101m"
            elif self.bk_color == BrightGreen:
                ret += "102m"
            elif self.bk_color == BrightYellow:
                ret += "103m"
            elif self.bk_color == BrightBlue:
                ret += "104m"
            elif self.bk_color == BrightPurple:
                ret += "105m"
            elif self.bk_color == BrightAqua:
                ret += "106m"
            elif self.bk_color == BrightWhite:
                ret += "107m"
            elif self.fg_color != Default and self.fg_color != SystemColor:
                ret += "m"

        if self.fg_color == SystemColor or self.bk_color == SystemColor:
            ret = "\033[0m" + ret

        return ret

    def __repr__(self):
        return "<%s instance fg:%s bk:%s>" % (self.__class__.__name__, color_to_str(self.fg_color), color_to_str(self.bk_color))


is_win32 = sys.platform == 'win32'
if is_win32:

    import ctypes

    def get_color():
        handle = ctypes.windll.kernel32.GetStdHandle(-12)
        string_buffer = ctypes.create_string_buffer(22)
        ret = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, string_buffer)
        wattr = 0
        if ret:
            import struct
            (bufx, bufy, curx, cury, wattr, left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", string_buffer.raw)

        if wattr > 0:
            return wattr

    # get default color of current console
    tmp = get_color()
    if tmp is not None:
        default_color = ConsoleColor(tmp & 0xf, tmp >> 4)
        default_color.Foreground(default_color.map_color(default_color.Foreground()))
        default_color.Background(default_color.map_color(default_color.Background()))
    else:
        default_color = ConsoleColor(0, 0)


def parse_color(str):
    tmp = str.lower()
    tmp = tmp.split(':')
    if len(tmp) > 2:
        raise OptionValueError("Error: to many ':' in definition of color. Value seen %s" % str)
    elif len(tmp) == 1:
        fg = tmp[0]
        bk = 'default'
    else:
        fg, bk = tmp

    def _get_col(col):
        if col in ['0', 'black', 'blk']:
            return Black
        elif col in ['1', 'red', 'r']:
            return Red
        elif col in ['2', 'green', 'g']:
            return Green
        elif col in ['3', 'yellow', 'y']:
            return Yellow
        elif col in ['4', 'blue', 'b']:
            return Blue
        elif col in ['5', 'purple', 'magenta', 'p', 'm']:
            return Purple
        elif col in ['6', 'aqua', 'cyan', 'a', 'c']:
            return Aqua
        elif col in ['7', 'white', 'lightgrey', 'lightgray', 'w', 'lg']:
            return White
        elif col in ['8', 'gray', 'grey']:
            return Gray
        elif col in ['9', 'brightred', 'br']:
            return BrightRed
        elif col in ['10', 'brightgreen', 'bg']:
            return BrightGreen
        elif col in ['11', 'brightyellow', 'by']:
            return BrightYellow
        elif col in ['12', 'brightblue', 'bb']:
            return BrightBlue
        elif col in ['13', 'brightpurple', 'brightmagenta', 'bp', 'bm']:
            return BrightPurple
        elif col in ['14', 'brightaqua', 'brightcyan', 'ba', 'bc']:
            return BrightAqua
        elif col in ['15', 'brightwhite', 'bw']:
            return BrightWhite
        elif col in ['default']:
            return Default
        elif col in ['bright', 'bold']:
            return Bright
        elif col in ['dim']:
            return Dim
        else:
            raise OptionValueError('Error: Invalid color value "%s"' % col)
    return ConsoleColor(_get_col(fg), _get_col(bk))
