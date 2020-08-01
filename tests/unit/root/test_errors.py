import unittest
from parts.errors import *


class TestErrors(unittest.TestCase):

    def setUp(self):
        pass

    def test_list_endwith(self):
        """Test list_endwith method"""
        string = "myfile.txt"
        self.assertEqual(True, list_endwith(string, [".txt", ".log"]))
        self.assertEqual(False, list_endwith(string, [".dat", ".tmp"]))

    # TODO: Test cases when stack starts not in SConstruct or .parts file
    # Jason: the current code is again in a few cases reporting the wrong
    # locations on the stack. these issues might be better tested with gold
    # tests
    #def test_SetPartStackFrameInfo(self):
        #"""Test that SetPartStackFrameInfo() sets frame to the SConstruct line with 'unittest.TextTestRunner' when this code is executed via 'scons SConsruct'"""
        #SetPartStackFrameInfo()
        #filename, line, routine, content = GetPartStackFrameInfo()
        #self.assertNotEqual(-1, filename.find("SConstruct"))
        #self.assertNotEqual(-1, content.find("unittest.TextTestRunner"))

    def test_ResetPartStackFrameInfo(self):
        """Test that ResetPartStackFrameInfo() resets length of 'glb.part_frame' to 0"""
        ResetPartStackFrameInfo()
        self.assertEqual(0, len(glb.part_frame))
