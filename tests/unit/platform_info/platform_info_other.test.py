import unittest
import SCons.Script
from parts.platform_info import SystemPlatform,target_convert
from parts.reporter import PartRuntimeError
import parts.settings as settings


class TestPlatformFunctions(unittest.TestCase):

    def setUp(self):
        self.env=settings.DefaultSettings().Environment() 
# A few tests below are commented out since they give Platform Specific outputs
    def test_platform_functions1(self):
#        s1 = ChipArchitecture()
#        self.assertEqual(s1,'x86_64')
        pass
        
    def test_platform_functions2(self):
#        s1 = OSBit()
#        self.assertEqual(s1,64)
        pass
        
    def test_platform_functions3(self):
#        s1 = target_convert('posix')
#        self.assertEqual(s1,'posix-x86_64')
        pass        
        
    def test_platform_functions4(self):
        s1 = target_convert('posix-x86')
        self.assertEqual(s1,'posix-x86')        