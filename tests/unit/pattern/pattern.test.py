import unittest
import SCons.Script
from parts.pattern import *


class TestPattern(unittest.TestCase):

    def setUp(self):
        pass

    def test_pattern1(self):
        filelist = Pattern(src_dir='./pattern', includes=['*.xml']).files()
        self.assertEqual(set(filelist), set([
            os.path.normpath('pattern/aaa.xml'),
            os.path.normpath('pattern/aaa/aaa.xml')
        ]))

   # def test_pattern2(self):  #This fails because Pattern() returns absolute path instead of relative
        #filelist = Pattern(src_dir='./pattern', includes=['*.xml']).files('aaa')
        # self.assertEqual(set(filelist),set(['pattern\\aaa\\aaa.xml']))

    def test_pattern3(self):
        filelist = Pattern(src_dir='./pattern', includes=['*.xml', '*.cpp']).files()
        self.assertEqual(set(filelist), set([
            os.path.normpath('pattern/aaa.xml'),
            os.path.normpath('pattern/bbb.cpp'),
            os.path.normpath('pattern/aaa/aaa.xml')
        ]))

    def test_pattern4(self):
        filelist = Pattern(src_dir='./pattern', includes=['*.xml', '*.cpp', '*.h'], excludes=['*.h']).files()
        self.assertEqual(set(filelist), set([
            os.path.normpath('pattern/aaa.xml'),
            os.path.normpath('pattern/bbb.cpp'),
            os.path.normpath('pattern/aaa/aaa.xml')
        ]))

    def test_pattern5(self):
        filelist = Pattern(src_dir='./pattern', includes=['*.xml', '*.cpp', '*.h'], excludes=['ccc.h']).files()
        self.assertEqual(set(filelist), set([
            os.path.normpath('pattern/aaa.xml'),
            os.path.normpath('pattern/bbb.cpp'),
            os.path.normpath('pattern/ddd.h'),
            os.path.normpath('pattern/aaa/aaa.xml')
        ]))

    def test_pattern6(self):
        filelist = Pattern(src_dir='./pattern', includes=['*.xml', '*.cpp', '*.h'], excludes=['.\\aaa\\*', './aaa/*']).files()
        self.assertEqual(set(filelist), set([
            os.path.normpath('pattern/aaa.xml'),
            os.path.normpath('pattern/bbb.cpp'),
            os.path.normpath('pattern/ccc.h'),
            os.path.normpath('pattern/ddd.h')
        ]))

    def test_pattern7(self):
        filelist = Pattern(src_dir='./pattern', includes=['aaa.xml', '*.cpp', '*.h'], excludes=['']).files()
        self.assertEqual(set(filelist), set([
            os.path.normpath('pattern/aaa.xml'),
            os.path.normpath('pattern/bbb.cpp'),
            os.path.normpath('pattern/ccc.h'),
            os.path.normpath('pattern/ddd.h')
        ]))

    def test_pattern8(self):
        filelist = Pattern(src_dir='./pattern', includes=['*.xml', '*.cpp', '*.h'], excludes=['??c.h']).files()
        self.assertEqual(set(filelist), set([
            os.path.normpath('pattern/aaa.xml'),
            os.path.normpath('pattern/bbb.cpp'),
            os.path.normpath('pattern/ddd.h'),
            os.path.normpath('pattern/aaa/aaa.xml')
        ]))

    def test_pattern9(self):
        filelist = Pattern(src_dir='./pattern', includes=['*.xml', '*.cpp', '*.h'], excludes=['[a-c][a-c][a-c].h']).files()
        self.assertEqual(set(filelist), set([
            os.path.normpath('pattern/aaa.xml'),
            os.path.normpath('pattern/bbb.cpp'),
            os.path.normpath('pattern/ddd.h'),
            os.path.normpath('pattern/aaa/aaa.xml')]))

    def test_pattern10(self):
        filelist = Pattern(src_dir='./pattern', includes=['*.xml', '*.cpp', '*.h'], excludes=['[!c][!c][!c].h']).files()
        self.assertEqual(set(filelist), set([
            os.path.normpath('pattern/aaa.xml'),
            os.path.normpath('pattern/bbb.cpp'),
            os.path.normpath('pattern/ccc.h'),
            os.path.normpath('pattern/aaa/aaa.xml')]))

    def test_pattern11(self):  # Possible Bug : This Test Fails because excludes override includes and so it returns a empty list. Though I think such a situation is not unimaginable
        filelist = Pattern(src_dir='./pattern', includes=['aaa.xml'], excludes=['*']).files()
        self.assertEqual(set(filelist), set([os.path.normpath('pattern/aaa.xml')]))
