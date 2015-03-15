import sys
from parts.tool_mapping import *
from parts.platform_info import *
import parts.settings as settings
import unittest


is_win32=False
is_linux=False
if sys.platform == 'win32':
    is_win32=True
elif sys.platform.startswith('linux'):
    is_linux=True

class Test_tool_mapping(unittest.TestCase):

    def setUp(self):
        self.env=settings.DefaultSettings().Environment()

    if is_win32:
        def test_ToolChain(self):
            """Test that if 'cl' toolchain is created then 'msvc' tool is in the list of 'CONFIGURED_TOOLS' env variable"""
            from SCons.Script.SConscript import SConsEnvironment
            SConsEnvironment.ToolChain(self.env, [('cl', None)])
            self.assertEqual(True, 'msvc' in self.env['CONFIGURED_TOOLS'])

        def test_get_tools(self):
            """Test that 'get_tools' returns exactly 1 instance for 'wdk' tool, some instances for 'cl 9.0' tool and 0 instances for 'cl 0.0' tool"""
            tools = get_tools(self.env, [('wdk', None)])
            self.assertEqual(len(tools), 1)
            self.assertEqual(tools[0][0], 'wdk')

            tools = get_tools(self.env, [('cl', '9.0')])
            self.assertNotEqual(len(tools), 0)

            tools = get_tools(self.env, [('cl', '0.0')])
            self.assertNotEqual(len(tools), 0)
    elif is_linux:
        def test_ToolChain(self):
            """Test that if 'gcc' toolchain is created then 'gcc' and 'g++' tools are in the list of 'CONFIGURED_TOOLS' env variable"""
            from SCons.Script.SConscript import SConsEnvironment
            SConsEnvironment.ToolChain(self.env, [('gcc', None)])
            self.assertEqual(True, 'gcc' in self.env['CONFIGURED_TOOLS'])
            self.assertEqual(True, 'g++' in self.env['CONFIGURED_TOOLS'])

        def test_get_tools(self):
            """Test that 'get_tools' returns exactly 1 instance for 'c++' tool, some instances for 'intelc 11.1' tool and 0 instances for 'intelc 0.0' tool"""
            tools = get_tools(self.env, [('c++', None)])
            self.assertEqual(len(tools), 1)
            self.assertEqual(tools[0][0], 'c++')

            tools = get_tools(self.env, [('intelc', '11.1')])
            self.assertNotEqual(len(tools), 0)

            tools = get_tools(self.env, [('intelc', '0.0')])
            self.assertNotEqual(len(tools), 0)
