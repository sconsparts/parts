import os
import shutil
import sys
import tempfile
from parts.tool_mapping import *
from parts.platform_info import *
import parts.api as api
import parts.settings as settings
import parts.tool_mapping as tool_mapping
import unittest


is_win32 = False
is_linux = False
if sys.platform == 'win32':
    is_win32 = True
elif sys.platform.startswith('linux'):
    is_linux = True


class Test_tool_mapping(unittest.TestCase):

    def setUp(self):
        self.env = settings.DefaultSettings().Environment()

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


class Test_tool_load_failure_reporting(unittest.TestCase):
    '''
    A tool name that cannot be resolved and a tool module that raises while
    loading are different problems and have to report differently. Reporting the
    second as "Unknown ToolChain or Tool" hides the real error: an import-time
    failure anywhere in a tool module, or in anything it imports, reads as a
    misspelled tool name and sends you looking in the wrong place.
    '''

    def setUp(self):
        self.env = settings.DefaultSettings().Environment()
        self.reported = []

        # error_msgf exits by default; capture instead so the flow can continue
        self._real_error_msgf = api.output.error_msgf

        def capture(sfmt, *lst, **kw):
            self.reported.append(sfmt.format(*lst))
        api.output.error_msgf = capture

        # get_tools caches the toolpath in a module global on first use. Seed it so
        # the tests are not affected by what is installed on the machine.
        # getattr/setattr avoid the private-name mangling a plain attribute
        # reference would get inside a class body.
        self._real_tools_dirs = getattr(tool_mapping, '__tools_dirs', None)
        self.tooldir = tempfile.mkdtemp()
        setattr(tool_mapping, '__tools_dirs', [self.tooldir])

    def tearDown(self):
        api.output.error_msgf = self._real_error_msgf
        if self._real_tools_dirs is None:
            try:
                delattr(tool_mapping, '__tools_dirs')
            except AttributeError:
                pass
        else:
            setattr(tool_mapping, '__tools_dirs', self._real_tools_dirs)
        shutil.rmtree(self.tooldir, ignore_errors=True)

    def test_unknown_tool_name_reports_where_it_looked(self):
        get_tools(self.env, [('no_such_tool_anywhere', None)])
        self.assertEqual(len(self.reported), 1)
        msg = self.reported[0]
        self.assertIn('Unknown ToolChain or Tool', msg)
        self.assertIn('no_such_tool_anywhere', msg)
        # the searched toolpath is what tells you whether a parts-site overlay
        # was picked up at all
        self.assertIn('Searched:', msg)
        self.assertIn(self.tooldir, msg)

    def test_tool_that_raises_reports_the_exception_and_traceback(self):
        with open(os.path.join(self.tooldir, 'boomtool.py'), 'w') as f:
            # the shape of the real bug: a name the module never bound. This was
            # a merge that kept one branch's import block and the other's call site.
            f.write('parts.common.make_list([])\n')

        get_tools(self.env, [('boomtool', None)])
        self.assertEqual(len(self.reported), 1)
        msg = self.reported[0]
        self.assertIn('boomtool', msg)
        self.assertIn('NameError', msg)
        self.assertIn('Traceback', msg)
        # it is not an unknown name, and must not claim to be
        self.assertNotIn('Unknown ToolChain or Tool', msg)
