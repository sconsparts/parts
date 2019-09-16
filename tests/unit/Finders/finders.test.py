
#################
# for easy testing
import sys
##############

win32 = sys.platform == 'win32'
import unittest
from parts.tools.Common.Finders import *


# tests for Finder objects

# Path

class TestPathFinder(unittest.TestCase):

    def setUp(self):
        pass

    def test_find(self):
        p = PathFinder([
            '../../fakepath',
            '../../samples'
        ])
        self.assertEqual(p(), '../../samples')

    def test_no_find(self):
        p = PathFinder([
            '../../fakepath',
            '../fakepath4'
        ])
        self.assertEqual(p(), None)


# Enviroment


class TestEnvFinder(unittest.TestCase):

    def setUp(self):
        os.environ['PARTS_TEST_VALUE'] = '/fakepath/subpath/a/b/c/'

    def tearDown(self):
        del os.environ['PARTS_TEST_VALUE']

    def test_find(self):
        p = EnvFinder([
            'fakepath',
            'PARTS_TEST_VALUE'
        ])

        self.assertEqual(p(), '/fakepath/subpath/a/b/c/')

    def test_no_find(self):
        p = EnvFinder([
            '../fakepath',
            '../fakepath4'
        ])

        self.assertEqual(p(), None)

    def test_find_relpath(self):
        p = EnvFinder([
            'fakepath',
            'PARTS_TEST_VALUE'
        ],
            '../../../'
        )
        self.assertEqual(p(), os.path.normpath('/fakepath/subpath'))

    def test_no_find_relpath(self):
        p = EnvFinder([
            'fakepath',
            'fakepath4'
        ],
            '../../../'
        )
        self.assertEqual(p(), None)

# registry .. window only test
if win32:
    class TestRegFinder(unittest.TestCase):

        def setUp(self):
            pass

        def test_find(self):
            p = RegFinder([
                'Software\\fakepath',
                'Software\\Microsoft\\Windows\\CurrentVersion\\ProgramFilesDir'
            ])
            r = p()
            self.assertTrue(r == 'C:\\Program Files (x86)' or r == 'C:\\Program Files')

        def test_no_find(self):
            p = RegFinder([
                'Software\\fakepath',
                'Software\\fakepath4'
            ])

            self.assertEqual(p(), None)

        def test_find_relpath(self):
            p = RegFinder([
                'Software\\fakepath',
                'Software\\Microsoft\\Windows\\CurrentVersion\\ProgramFilesDir'
            ],
                '../'
            )

            self.assertEqual(p(), 'C:\\')

        def test_no_find_relpath(self):
            p = RegFinder([
                'Software\\fakepath',
                'Software\\fakepath4',
            ],
                '../'
            )
            self.assertEqual(p(), None)
else:
    class TestRegFinder(unittest.TestCase):

        def setUp(self):
            pass


# tests for ScriptFincder object

class TestScriptFinder(unittest.TestCase):

    def setUp(self):
        self.env = SCons.Script.Environment(INSTALL_ROOT='./testdata/', tools=[])

    def test_exists(self):
        p = ScriptFinder('${INSTALL_ROOT}testvars.cmd')
        self.assertEqual(p(self.env), os.path.normpath('./testdata/testvars.cmd'))

    def test_no_exists(self):
        p = ScriptFinder('${INSTALL_ROOT}fakevars.cmd')
        self.assertEqual(p(self.env), None)
