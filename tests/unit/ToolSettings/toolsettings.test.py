import sys
from parts.tools.Common.ToolSetting import *
from parts.tools.Common.ToolInfo import *
from parts.tools.Common.Finders import *
from parts.platform_info import *
import unittest


if sys.platform.startswith('linux'):
    platformStr = 'posix'
else:
    platformStr = sys.platform

# our MacOS has the platform specified as darwin-x86
has64bit = sys.platform != 'darwin'
toolArch = 'x86_64' if has64bit else 'x86'

# tests for ToolSettings objects


class TestToolSettings(unittest.TestCase):

    def setUp(self):
        self.env = SCons.Script.Environment(tools=[], HOST_PLATFORM=HostSystem(),
                                            TARGET_PLATFORM=HostSystem())

    def test_exists(self):
        """Creates dummy tool 'mycl' and tests that it exists for specified platform"""
        ts = ToolSetting('mycl')

        ts.Register(
            hosts=[SystemPlatform(platformStr, toolArch)],
            targets=[SystemPlatform(platformStr, toolArch)],
            info=[
                ToolInfo(
                    version='0.0',
                    install_scanner=[PathFinder([r'./testdata'])],
                    script=None,
                    subst_vars={},
                    shell_vars={'PATH': r'./testdata/vc/bin'},
                    test_file='cl.exe'
                )
            ]
        )

        self.assertEqual(True, ts.Exists(self.env))
        if has64bit:
            self.assertEqual(False, ts.Exists(self.env,
                                              TARGET_PLATFORM=SystemPlatform(platformStr, 'x86')))

    def test_get_latest_known_version1(self):
        """Creates dummy tool 'mycl' with versions 0.0 and 1.0, query for exact 0.0 version and
        tests that exactly this version is found"""
        ts = ToolSetting('mycl')

        ts.Register(
            hosts=[SystemPlatform(platformStr, toolArch)],
            targets=[SystemPlatform(platformStr, toolArch)],
            info=[
                ToolInfo(
                    version='0.0',
                    install_scanner=[PathFinder([r'./testdata'])],
                    script=None,
                    subst_vars={},
                    shell_vars={'PATH': r'./testdata/vc/bin'},
                    test_file='cl.exe'
                ),
                ToolInfo(
                    version='1.0',
                    install_scanner=[PathFinder([r'./testdata'])],
                    script=None,
                    subst_vars={},
                    shell_vars={'PATH': r'./testdata/vc/bin'},
                    test_file='cl.exe'
                ),
            ]
        )

        key = ts.get_cache_key(self.env)
        ts.query_for_exact(self.env, key, '0.0')
        self.assertEqual('0.0', ts.get_latest_known_version(key))

    def test_get_latest_known_version2(self):
        """Creates dummy tool 'mycl' with versions 0.0 and 1.0, query for known version and
        tests that the latest 1.0 version is found"""
        ts = ToolSetting('mycl')

        ts.Register(
            hosts=[SystemPlatform(platformStr, toolArch)],
            targets=[SystemPlatform(platformStr, toolArch)],
            info=[
                ToolInfo(
                    version='0.0',
                    install_scanner=[PathFinder([r'./testdata'])],
                    script=None,
                    subst_vars={},
                    shell_vars={'PATH': r'./testdata/vc/bin'},
                    test_file='cl.exe'
                ),
                ToolInfo(
                    version='1.0',
                    install_scanner=[PathFinder([r'./testdata'])],
                    script=None,
                    subst_vars={},
                    shell_vars={'PATH': r'./testdata/vc/bin'},
                    test_file='cl.exe'
                ),
            ]
        )

        key = ts.get_cache_key(self.env)
        ts.query_for_known(self.env, key)
        self.assertEqual('1.0', ts.get_latest_known_version(key))

    def test_get_shell_env1(self):
        """Creates dummy tool 'mycl' and tests that tool environment has proper env variables
        set: 'INSTALL_ROOT', 'TOOL' and 'VERSION'"""
        ts = ToolSetting('mycl')

        ts.Register(
            hosts=[SystemPlatform(platformStr, toolArch)],
            targets=[SystemPlatform(platformStr, toolArch)],
            info=[
                ToolInfo(
                    version='0.0',
                    install_scanner=[PathFinder([r'./testdata'])],
                    script=None,
                    subst_vars={},
                    shell_vars={'PATH': r'./testdata/vc/bin'},
                    test_file='cl.exe'
                )
            ]
        )

        shellEnv, tsEnv = ts.get_shell_env(self.env)
        self.assertEqual(tsEnv['INSTALL_ROOT'], 'testdata')
        self.assertEqual(tsEnv['TOOL'], 'cl.exe')
        self.assertEqual(tsEnv['VERSION'], '0.0')

    def test_MatchVersionNumbers(self):
        """Test MatchVersionNumbers. Create various version strings including major, minor,
        revision numbers etc."""
        self.assertEqual(MatchVersionNumbers('1.1', '1.1.-1'), True)
        self.assertEqual(MatchVersionNumbers('1.2.3', '1'), True)
        self.assertEqual(MatchVersionNumbers('1.2.3', '1.2'), True)
        self.assertEqual(MatchVersionNumbers('1.2.3', '1.2.3'), True)
        self.assertEqual(MatchVersionNumbers('1.2.3', '1.2.3.4'), True)
        self.assertEqual(MatchVersionNumbers('1.2.3.', '1.2.3.4'), True)
        self.assertEqual(MatchVersionNumbers('1.2.3.4.', '1.2.3.4'), True)
        self.assertEqual(MatchVersionNumbers('1.2.3.4', '1.2.3.5'), True)

        self.assertEqual(MatchVersionNumbers('1.2', '12'), False)
        self.assertEqual(MatchVersionNumbers('1.2', '1.3'), False)
        self.assertEqual(MatchVersionNumbers('1.2.3', '1.2.4'), False)

        # This code raises the Exception in MatchVersionNumbers. I believe that
        # MatchVersionNumbers should handle the Exception and return True/False
        # try:
        self.assertEqual(MatchVersionNumbers('1.', '1'), True)
        # except:
        #    pass

        # This code raises the Exception in MatchVersionNumbers. I believe that
        # MatchVersionNumbers should handle the Exception and return True/False
        # try:
        self.assertEqual(MatchVersionNumbers('1.', '1.1'), True)
        # except:
        #    pass
