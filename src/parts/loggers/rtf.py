

import os
import sys

import parts.color as color
import parts.logger as logger
import SCons.Script

# rtf Simple logger. Probally needs more work.


def RtfColorIndex(col):
    global _RtfColorIndex
    try:
        return _RtfColorIndex.get(col) or 0
    except NameError:
        _RtfColorIndex = dict((
            (color.Black, 17),
            (color.Blue, 2),
            (color.Green, 3),
            (color.Cyan, 4),
            (color.Red, 5),
            (color.Magenta, 6),
            (color.Yellow, 7),
            (color.White, 8),
            (color.Gray, 9),
            (color.BrightBlue, 10),
            (color.BrightGreen, 11),
            (color.BrightCyan, 12),
            (color.BrightRed, 13),
            (color.BrightMagenta, 14),
            (color.BrightYellow, 15),
            (color.BrightWhite, 16),
        ))
        return _RtfColorIndex.get(col) or 0


class rtf(logger.Logger):

    def __init__(self, dir, file):
        if os.path.exists(dir) == False:
            os.makedirs(dir)
        if file.endswith(".rtf") == False:
            file += ".rtf"
        self.m_file = open(os.path.join(dir, file), "w")

        self.colors = SCons.Script.GetOption('use_color')
        self.fg_color = 0
        self.writeheader()
        super(rtf, self).__init__(dir, file)

    def writeheader(self):
        self.m_file.write("{\\rtf1\\fbidis\\ansi\\ansicpg1252")
        self.m_file.write('''{\\colortbl;red0\\green0\\blue128;\\red0\\green128\\blue0;\\red0\\green128\\blue128;\
\\red128\\green0\\blue0;\\red1\\green36\\blue86;\\red238\\green237\\blue240;\\red192\\green192\\blue192;\
\\red128\\green128\\blue128;\\red0\\green0\\blue255;\\red0\\green255\\blue0;\\red0\\green255\\blue255;\
\\red255\\green0\\blue0;\\red255\\green0\\blue255;\\red255\\green255\\blue0;\\red255\\green255\\blue255;\\red0\\green0\\blue0;}\n''')
        self.m_file.write('\\viewkind4\\pard')

    def out_color(self, col):
        fg = col.Foreground()
        if fg == color.Bright:
            if self.fg_color < 8:
                fg = self.fg_color + 8
            else:
                fg = self.fg_color
        elif fg == color.Dim:
            if self.fg_color > 8:
                fg = self.fg_color - 8
            else:
                fg = self.fg_color
        else:
            self.fg_color = fg

        self.m_file.write("\\cf1\\cf%s " % (RtfColorIndex(self.fg_color)))

    def writestr(self, msg):
        for c in msg:
            if c == '\t':
                self.m_file.write('\\tab')
            elif c == '\\':
                self.m_file.write('\\\\')
            elif c == '{':
                self.m_file.write('\\{')
            elif c == '}':
                self.m_file.write('\\}')
            elif c == '\n':
                self.m_file.write('\\par\n')
            else:
                self.m_file.write(c)

    def logout(self, msg):
        self.out_color(self.colors['stdout'])
        self.writestr(msg)

    def logerr(self, msg):
        self.out_color(self.colors['stderr'])
        self.writestr(msg)

    def logwrn(self, msg):
        self.out_color(self.colors['stdwrn'])
        self.writestr(msg)

    def logmsg(self, msg):
        self.out_color(self.colors['stdmsg'])
        self.writestr(msg)

    def logtrace(self, msg):
        self.out_color(self.colors['stdtrace'])
        self.writestr(msg)

    def logverbose(self, msg):
        self.out_color(self.colors['stdverbose'])
        self.writestr(msg)

    def shutdown(self):
        self.m_file.write("}")
        self.m_file.close()

    def __del__(self):
        try:
            self.m_file.close()
        except Exception:
            pass
