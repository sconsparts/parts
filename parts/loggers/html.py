# simple HTML logger


import SCons.Script
import parts.logger as logger
import parts.color as color
import os
import sys


# html Simple logger. Probally needs more work.


def RtfColorIndex(col):
    global _RtfColorIndex
    try:
        return _RtfColorIndex.get(col) or "black"
    except NameError:
        _RtfColorIndex = dict((
            (color.Black, "black"),
            (color.Blue, "blue"),
            (color.Green, "green"),
            (color.Cyan, "aqua"),
            (color.Red, "red"),
            (color.Magenta, "purple"),
            (color.Yellow, "yellow"),
            (color.White, "white"),
            (color.Gray, "gray"),
            (color.BrightBlue, "brightblue"),
            (color.BrightGreen, "brightgreen"),
            (color.BrightCyan, "brightaqua"),
            (color.BrightRed, "brightred"),
            (color.BrightMagenta, "brightmagenta"),
            (color.BrightYellow, "brightyellow"),
            (color.BrightWhite, "brightwhite"),
        ))
        return _RtfColorIndex.get(col) or "black"


class html(logger.Logger):

    def __init__(self, dir, file):
        if os.path.exists(dir) == False:
            os.makedirs(dir)
        if file.endswith(".html") == False:
            file += ".html"
        self.m_file = open(os.path.join(dir, file), "w")
        super(html, self).__init__(dir, file)

        self.colors = SCons.Script.GetOption('use_color')
        self.fg_color = color.White
        self.default_color = color.White
        self.writeheader()

    def writeheader(self):
        self.m_file.write('''<html>
<head>
    <title></title>
    <style type="text/css">
        .black
        {
            color: #000000;
        }
        .red
        {
            color: #800000;
        }
        .blue
        {
            color: #000080;
        }
        .green
        {
            color: #008000;
        }
        .yellow
        {
            color: #808000;
        }
        .aqua
        {
            color: #008080;
        }
        .purple
        {
            color: #800080;
        }
        .white
        {
            color: #808080;
        }
        .grey
        {
            color: #C0C0C0;
        }
        .brightred
        {
            color: #FF0000;
        }
        .brightblue
        {
            color: #0000FF;
        }
        .brightgreen
        {
            color: #00FF00;
        }
        .brightyellow
        {
            color: #FFFF00;
        }
        .brightaqua
        {
            color: #00FFFF;
        }
        .brightpurple
        {
            color: #FF00FF;
        }
        .brightwhite
        {
            color: #FFFFFF;
        }
    </style>
</head>
<body bgcolor="#000000">
        ''')

    def out_color(self, col):
        fg = col.Foreground()
        if fg == color.Bright:
            if self.default_color < 8:
                fg = self.default_color + 8
            else:
                fg = self.default_color
        elif fg == color.Dim:
            if self.default_color > 8:
                fg = self.default_color - 8
            else:
                fg = self.default_color

        self.fg_color = fg
        with self._lock:
            self.m_file.write("<span class=\"%s\">" % (RtfColorIndex(self.fg_color)))

    def writestr(self, msg):
        with self._lock:
            for c in msg:
                if c == '>':
                    self.m_file.write('&gt')
                elif c == '<':
                    self.m_file.write('&lt')
                elif c == '&':
                    self.m_file.write('&amp')
                elif c == '\n':
                    self.m_file.write('<br/>')
                else:
                    self.m_file.write(c)
            self.m_file.write("</span>\n")

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
        with self._lock:
            self.m_file.write("</body></html>")
        self.m_file.close()

    def __del__(self):
        try:
            self.m_file.close()
        except:
            pass
