import unittest
import SCons.Script
from parts.platform_info import SystemPlatform
from parts.reporter import PartRuntimeError
import parts.settings as settings


class TestPlatform(unittest.TestCase):

    def setUp(self):
        self.env = settings.DefaultSettings().Environment()

    def test_platform1(self):
        s1 = SystemPlatform('win32', 'x86_64')
        self.assertEqual(s1, 'win32-x86_64')

    def test_platform2(self):
        s1 = SystemPlatform('any', 'x86')
        self.assertEqual(s1, 'any-x86')

    def test_platform3(self):
        s1 = SystemPlatform('win32', 'x86_64')
        s2 = SystemPlatform('win32', 'x86_64')
        self.assertTrue(s1 == s2)

    def test_platform4(self):
        s1 = SystemPlatform('win32', 'x86_64')
        s2 = SystemPlatform('win32', 'any')
        self.assertTrue(s1 == s2)

    def test_platform5(self):
        s1 = SystemPlatform('win32', 'x86_64')
        s2 = SystemPlatform('any', 'x86_64')
        self.assertTrue(s1 == s2)

    def test_platform6(self):
        s1 = SystemPlatform('win32', 'x86_64')
        s2 = SystemPlatform('any', 'any')
        self.assertTrue(s1 == s2)

    def test_platform7(self):
        try:
            # This should fail to create
            s1 = SystemPlatform('x86', 'win32')
        except PartRuntimeError as e:
            self.assertTrue(True)
            return
        self.assertTrue(False)

    def test_platform8(self):

        target_os = self.env['TARGET_OS']
        target_arch = self.env['TARGET_ARCH']

        s1 = SystemPlatform('any', 'any')
        self.env['TARGET_PLATFORM'] = s1
        self.assertEqual(self.env['TARGET_OS'], target_os)
        self.assertEqual(self.env['TARGET_ARCH'], target_arch)
        self.assertEqual(self.env['TARGET_PLATFORM'], "%s-%s" % (target_os, target_arch))

    def test_platform9(self):
        target_os = self.env['TARGET_OS']
        target_arch = self.env['TARGET_ARCH']
        if target_os == 'win32':
            new_os = 'posix'
        else:
            new_os = 'win32'

        if target_arch == 'x86':
            new_arch = 'x86_64'
        else:
            new_arch = 'x86'

        s1 = SystemPlatform(new_os, new_arch)
        self.env['TARGET_PLATFORM'] = s1
        self.assertEqual(self.env['TARGET_OS'], s1.OS)
        self.assertEqual(self.env['TARGET_ARCH'], s1.ARCH)

    def test_platform10(self):
        s1 = SystemPlatform('win32', 'x86')
        self.assertEqual(s1['OS'], 'win32')

    def test_platform11(self):
        s1 = SystemPlatform('win32', 'x86')
        self.assertEqual(s1['ARCH'], 'x86')

    def test_platform12(self):
        s1 = SystemPlatform('win32', 'x86')
        s1['ARCH'] = 'x86_64'
        self.assertEqual(s1, 'win32-x86_64')

    def test_platform13(self):
        s1 = SystemPlatform('win32', 'x86')
        s2 = s1
        self.assertEqual(s2, 'win32-x86')

    def test_platform14(self):
        s1 = SystemPlatform('win32', 'x86')
        s2 = s1.__deepcopy__()
        self.assertEqual(s2, 'win32-x86')

    def test_platform15(self):
        s1 = SystemPlatform('win32', 'x86')
        self.assertEqual(s1.OS, 'win32')

    def test_platform16(self):
        s1 = SystemPlatform('win32', 'x86')
        self.assertEqual(s1.ARCH, 'x86')

    def test_platform17(self):
        try:
            # This should fail to create
            s1 = SystemPlatform('foo', 'bar')
        except PartRuntimeError as e:
            self.assertTrue(True)
            return
        self.assertTrue(False)

    def test_platform18(self):
        try:
            # This should fail to create
            s1 = SystemPlatform('x86-win32')
        except PartRuntimeError as e:
            self.assertTrue(True)
            return
        self.assertTrue(False)
