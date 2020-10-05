import unittest
import SCons.Script
from parts.platform_info import SystemPlatform
from parts.reporter import PartRuntimeError
import parts.settings as settings


class TestSystemPlatform(unittest.TestCase):

    def setUp(self):
        self.env = settings.DefaultSettings().Environment()

    def test_eq_operator(self):
        p1 = SystemPlatform('posix-x86')
        self.assertEqual(p1, 'posix-x86')
        self.assertEqual(p1, 'x86')
        self.assertEqual(p1, 'posix')
        self.assertNotEqual(p1, 'win32-x86_64')
        self.assertNotEqual(p1, 'x86_64')
        self.assertNotEqual(p1, 'win32')
        self.assertNotEqual(p1, 'foobar')
        self.assertNotEqual(p1, 'foo-bar')

    def test_os(self):
        p1 = SystemPlatform('posix-x86')
        self.assertEqual(p1.OS, 'posix')
        p1.OS='linux'
        self.assertEqual(p1.OS, 'posix')
        p1.OS='win32'
        self.assertEqual(p1.OS, 'win32')
        p1 = SystemPlatform('posix')
        self.assertEqual(p1.OS, 'posix')

    def test_os_mapping(self):
        p1 = SystemPlatform()
        p1.OS='linux'
        self.assertEqual(p1.OS, 'posix')
        p1.OS='fedora'
        self.assertEqual(p1.OS, 'posix')
        
    def test_arch(self):
        p1 = SystemPlatform('posix-x86')
        self.assertEqual(p1.ARCH, 'x86')
        p1.ARCH='x86_64'
        self.assertEqual(p1.ARCH, 'x86_64')
        
        p1 = SystemPlatform('x86')
        self.assertEqual(p1.ARCH, 'x86')

    def test_arch_mapping(self):        
        p1 = SystemPlatform()
        p1.ARCH='i486'
        self.assertEqual(p1.ARCH, 'x86')
        p1.ARCH='em64t'
        self.assertEqual(p1.ARCH, 'x86_64')