import sys
win32 = sys.platform == 'win32'

import unittest
from parts.color import *
import SCons.Script


# tests for Finder objects


class TestConsoleColor(unittest.TestCase):

    def setUp(self):
        # self.env=SCons.Script.Environment(tools=[])
        pass

    def test_color_create1(self):

        # test the creation logic given standard colors
        c = ConsoleColor(Blue, Black)
        self.assertEqual(c.Foreground(), Blue)
        self.assertEqual(c.Background(), Black)

    def test_color_create2(self):

        # test the creation logic, default logic,implict
        c = ConsoleColor()
        self.assertEqual(c.Background(), Default)
        self.assertEqual(c.Foreground(), Default)

    def test_color_create3(self):

        # test the creation logic, Bold logic
        c = ConsoleColor(Bold, Bold)
        self.assertEqual(c.Background(), Default)
        self.assertEqual(c.Foreground(), Bold)

    def test_color_create4(self):

        # test the creation logic, default logic explict
        c = ConsoleColor(Default, Default)
        self.assertEqual(c.Background(), Default)
        self.assertEqual(c.Foreground(), Default)

    def test_color_SetGet(self):

        # test the setting and getting of a value
        c = ConsoleColor()
        c.Foreground(Green)
        self.assertEqual(c.Foreground(), Green)
        c.Background(Red)
        self.assertEqual(c.Background(), Red)

    def test_color_ansivalue_foreground(self):

        # test the setting and getting of a value as the ansi value we give to
        # the screen. simple forground test here
        c = ConsoleColor()

        c.Foreground(Black)
        self.assertEqual(c.ansi_value(), '\033[30m')

        c.Foreground(Red)
        self.assertEqual(c.ansi_value(), '\033[31m')

        c.Foreground(Green)
        self.assertEqual(c.ansi_value(), '\033[32m')

        c.Foreground(Yellow)
        self.assertEqual(c.ansi_value(), '\033[33m')

        c.Foreground(Blue)
        self.assertEqual(c.ansi_value(), '\033[34m')

        c.Foreground(Purple)
        self.assertEqual(c.ansi_value(), '\033[35m')

        c.Foreground(Aqua)
        self.assertEqual(c.ansi_value(), '\033[36m')

        c.Foreground(White)
        self.assertEqual(c.ansi_value(), '\033[37m')

    def test_color_ansivalue_foreground_bright(self):

        # test the setting and getting of a value as the ansi value we give to
        # the screen. simple forground test here
        c = ConsoleColor()

        c.Foreground(Gray)
        self.assertEqual(c.ansi_value(), '\033[1;30m')

        c.Foreground(BrightRed)
        self.assertEqual(c.ansi_value(), '\033[1;31m')

        c.Foreground(BrightGreen)
        self.assertEqual(c.ansi_value(), '\033[1;32m')

        c.Foreground(BrightYellow)
        self.assertEqual(c.ansi_value(), '\033[1;33m')

        c.Foreground(BrightBlue)
        self.assertEqual(c.ansi_value(), '\033[1;34m')

        c.Foreground(BrightPurple)
        self.assertEqual(c.ansi_value(), '\033[1;35m')

        c.Foreground(BrightAqua)
        self.assertEqual(c.ansi_value(), '\033[1;36m')

        c.Foreground(BrightWhite)
        self.assertEqual(c.ansi_value(), '\033[1;37m')

    def test_color_ansivalue_background(self):

        # test the setting and getting of a value as the ansi value we give to
        # the screen. simple background test here
        c = ConsoleColor()

        c.Background(Black)
        self.assertEqual(c.ansi_value(), '\033[40m')

        c.Background(Red)
        self.assertEqual(c.ansi_value(), '\033[41m')

        c.Background(Green)
        self.assertEqual(c.ansi_value(), '\033[42m')

        c.Background(Yellow)
        self.assertEqual(c.ansi_value(), '\033[43m')

        c.Background(Blue)
        self.assertEqual(c.ansi_value(), '\033[44m')

        c.Background(Purple)
        self.assertEqual(c.ansi_value(), '\033[45m')

        c.Background(Aqua)
        self.assertEqual(c.ansi_value(), '\033[46m')

        c.Background(White)
        self.assertEqual(c.ansi_value(), '\033[47m')

    def test_color_ansivalue_background_bright(self):

        # test the setting and getting of a value as the ansi value we give to
        # the screen. simple background test here
        c = ConsoleColor()

        c.Background(Gray)
        self.assertEqual(c.ansi_value(), '\033[100m')

        c.Background(BrightRed)
        self.assertEqual(c.ansi_value(), '\033[101m')

        c.Background(BrightGreen)
        self.assertEqual(c.ansi_value(), '\033[102m')

        c.Background(BrightYellow)
        self.assertEqual(c.ansi_value(), '\033[103m')

        c.Background(BrightBlue)
        self.assertEqual(c.ansi_value(), '\033[104m')

        c.Background(BrightPurple)
        self.assertEqual(c.ansi_value(), '\033[105m')

        c.Background(BrightAqua)
        self.assertEqual(c.ansi_value(), '\033[106m')

        c.Background(BrightWhite)
        self.assertEqual(c.ansi_value(), '\033[107m')

    def test_color_ansivalue_Complex(self):

        # test the setting and getting of a value as the ansi value we give to
        # the screen. Complex tests
        c = ConsoleColor(Bold)
        self.assertEqual(c.ansi_value(), '\033[1m')

        c = ConsoleColor(Default, Green)
        self.assertEqual(c.ansi_value(), '\033[42m')

        c.Foreground(Red)
        c.Background(Default)
        self.assertEqual(c.ansi_value(), '\033[31m')

        c.Background(Red)
        c.Foreground(Default)
        self.assertEqual(c.ansi_value(), '\033[41m')

        c.Foreground(Red)
        c.Background(SystemColor)
        self.assertEqual(c.ansi_value(), '\033[0m\033[31m')

        c.Background(Red)
        c.Foreground(SystemColor)
        self.assertEqual(c.ansi_value(), '\033[0m\033[41m')

        c = ConsoleColor(SystemColor)
        self.assertEqual(c.ansi_value(), '\033[0m')

    def test_color_sting_test(self):

        c = ConsoleColor(Blue, Black)
        str = "hello" + c + "world"

        self.assertEqual(str, "hello\033[34;40mworld")
