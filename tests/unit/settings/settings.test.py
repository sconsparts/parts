import sys
from parts.settings import *
import unittest


is_win32 = False
is_linux = False
if sys.platform == 'win32':
    is_win32 = True
elif sys.platform.startswith('linux'):
    is_linux = True


def _tester(item):
    return isinstance(item, str)


class Test_settings(unittest.TestCase):

    def setUp(self):
        pass

    def test_DefaultSettings_DefaultEnvironment(self):
        """Test that default environment is properly initialized, i.e. it has 'INSTALL' and 'ZIP' env variables set"""
        defEnv = DefaultSettings().DefaultEnvironment()
        self.assertEqual(defEnv.has_key('INSTALL'), True)
        self.assertEqual(defEnv.has_key('ZIP'), True)
        # TODO: Test for more default env vars

    def test_DefaultSettings_Environment(self):
        """Test that environment with additional custom env varaibles is properly created"""
        env = DefaultSettings().Environment(name1='val1', name2='val2')
        self.assertEqual(env['name1'], 'val1')
        self.assertEqual(env['name2'], 'val2')

    def test_All(self):
        """Test All class. Tester here checks that element in the list is the instance of str"""

        """Here some elements of the list are valid, i.e. instances of str"""
        someInst = All(1, '1', self, '', 0.1, str())
        self.assertEqual(someInst.Valid(_tester), False)
        self.assertEqual(someInst.GetValues(), (1, '1', self, '', 0.1, str()))

        """Here all elements of the list are valid, i.e. instances of str"""
        allInst = All('1', '', str())
        self.assertEqual(allInst.Valid(_tester), True)
        self.assertEqual(allInst.GetValues(), ('1', '', str()))

        """Here none elements of the list are valid, i.e. instances of str"""
        noneInst = All(1, self, 0.1)
        self.assertEqual(noneInst.Valid(_tester), False)
        self.assertEqual(noneInst.GetValues(), (1, self, 0.1))

    def test_OneOf(self):
        """Test OneOf class. Tester here checks that element in the list is the instance of str"""

        """Here some elements of the list are valid, i.e. instances of str"""
        someInst = OneOf(1, '1', self, '', 0.1, str())
        self.assertEqual(someInst.Valid(_tester), True)
        self.assertEqual(someInst.GetValues(_tester), ['1'])

        """Here all elements of the list are valid, i.e. instances of str"""
        allInst = OneOf('1', '', str())
        self.assertEqual(allInst.Valid(_tester), True)
        self.assertEqual(allInst.GetValues(_tester), ['1'])

        """Here none elements of the list are valid, i.e. instances of str"""
        noneInst = OneOf(1, self, 0.1)
        self.assertEqual(noneInst.Valid(_tester), False)
        self.assertEqual(noneInst.GetValues(_tester), [])

    def test_AnyOf(self):
        """Test AnyOf class. Tester here checks that element in the list is the instance of str"""

        """Here some elements of the list are valid, i.e. instances of str"""
        someInst = AnyOf(1, '1', self, '', 0.1, str())
        self.assertEqual(someInst.Valid(_tester), True)
        self.assertEqual(someInst.GetValues(_tester), ['1', '', str()])

        """Here all elements of the list are valid, i.e. instances of str"""
        allInst = AnyOf('1', '', str())
        self.assertEqual(allInst.Valid(_tester), True)
        self.assertEqual(allInst.GetValues(_tester), ['1', '', str()])

        """Here none elements of the list are valid, i.e. instances of str"""
        noneInst = AnyOf(1, self, 0.1)
        self.assertEqual(noneInst.Valid(_tester), False)
        self.assertEqual(noneInst.GetValues(_tester), [])
