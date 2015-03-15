import unittest
import parts.version_info as version_info
import SCons.Script

class TestVersionInfo(unittest.TestCase):

    def setUp(self):
        self.env = SCons.Script.Environment()

    def test_PartVersionString(self):
        """Test that PartVersionString contains _PARTS_VERSION"""
        from SCons.Script.SConscript import SConsEnvironment
        self.assertNotEqual(version_info.parts_version_text().find(version_info._PARTS_VERSION), -1)
        self.assertNotEqual(SConsEnvironment.PartVersionString(self.env).find(version_info._PARTS_VERSION), -1)

    def test_PartsExtensionVersion(self):
        """Test that PartsExtensionVersion coinsides with _PARTS_VERSION"""
        from SCons.Script.SConscript import SConsEnvironment
        self.assertEqual(version_info.PartsExtensionVersion(), version_info._PARTS_VERSION)
        self.assertEqual(SConsEnvironment.PartsExtensionVersion(self.env), version_info._PARTS_VERSION)

    def test_IsPartsExtensionVersionBeta(self):
        """Test that IsPartsExtensionVersionBeta returns correct value for custom defined _PARTS_VERSION"""
        from SCons.Script.SConscript import SConsEnvironment
        origVersion = version_info._PARTS_VERSION

        version_info._PARTS_VERSION = '0.10.0.Beta.10'
        self.assertEqual(version_info.is_parts_version_beta(), True)
        self.assertEqual(SConsEnvironment.IsPartsExtensionVersionBeta(self.env), True)

        version_info._PARTS_VERSION = '0.10.0.10'
        self.assertEqual(version_info.is_parts_version_beta(), False)
        self.assertEqual(SConsEnvironment.IsPartsExtensionVersionBeta(self.env), False)

        version_info._PARTS_VERSION = origVersion
