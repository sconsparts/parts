import sys
import os
import copy
win32 = sys.platform == 'win32'

import unittest
from parts.pieces.merge_script import *
import SCons.Script
import sys
is_win32 = False
is_linux = False
is_darwin = False
if sys.platform == 'win32':
    is_win32 = True
elif sys.platform.startswith('linux'):
    is_linux = True
elif sys.platform == 'darwin':
    is_darwin = True

# tests for Finder objects


class TestMergeScript(unittest.TestCase):

    def setUp(self):
        self.env = SCons.Script.Environment(tools=[])

    def test_normalize_env(self):
        newEnv = {}
        newEnv['MYENV'] = 'MYVALUE'

        osEnvCopy = copy.deepcopy(os.environ)
        for key in newEnv.keys():
            os.environ[key] = newEnv[key]
        keys = copy.deepcopy(newEnv.keys())
        keys.append('DUMMY')
        norm_env = normalize_env(self.env['ENV'], keys)
        os.environ = osEnvCopy

        for key in newEnv.keys():
            self.assertEqual(norm_env.get(key, None), newEnv[key])
        self.assertEqual(norm_env.get('DUMMY', None), None)

    if is_win32:
        def test_get_output(self):
            norm_env = normalize_env(self.env['ENV'])
            output = get_output(os.path.join('testdata', 'testvars.cmd'), args='dummy_arg1 dummy_arg2', shellenv=norm_env)
            # print 'output=' + str(output)
            expectedOutput = []
            expectedOutput.append(r'ARGTEST=dummy_arg1')
            expectedOutput.append(r'INCLUDE=C:\Program Files (x86)\joe\myinclude\INCLUDE;C:\foo\INCLUDE;oddvar;;;like this')
            expectedOutput.append(r'LIB=C:\Windows\someplace;C:\Program Files (x86)\joe\myinclude\LIB;C:\foo\lib;')
            expectedOutput.append(r'LIBPATH=C:\Windows\someplace;')
            for expectedOutputItem in expectedOutput:
                self.assertNotEqual(output.find(expectedOutputItem), -1)
    elif is_linux or is_darwin:
        def test_get_output(self):
            output = get_output(os.path.join('testdata', 'testvars.sh'), args='dummy_arg1 dummy_arg2', shellenv=self.env['ENV'])
            # print 'output=' + str(output)
            expectedOutput = []
            expectedOutput.append(r'ARGTEST=dummy_arg1')
            expectedOutput.append(r"INCLUDE='/usr/bin/joe/myinclude/INCLUDE:/opt/foo/INCLUDE:oddvar:::like this'")
            expectedOutput.append(r'LIB=/opt/someplace:/usr/bin/joe/myinclude/LIB:/opt/foo/lib:')
            expectedOutput.append(r'LIBPATH=/opt/someplace:')
            for expectedOutputItem in expectedOutput:
                # print 'analysing ' + str(expectedOutputItem)
                self.assertNotEqual(output.find(expectedOutputItem), -1)

    def test_parse_output(self):
        output = """key1=var1
key2= var2 var22
key3=
key4= var4
key5 var5
key6 =var6
key7 = var7
key8 == var8
        """
        parsed1 = parse_output(output)
        # print parsed
        self.assertEqual(parsed1['key1'], 'var1')
        self.assertEqual(parsed1['key2'], ' var2 var22')
        self.assertEqual(parsed1['key3'], '')
        self.assertEqual(parsed1['key4'], ' var4')
        self.assertEqual('key5' in parsed1, False)
        self.assertEqual('key6' in parsed1, False)
        self.assertEqual('key7' in parsed1, False)
        self.assertEqual('key8' in parsed1, False)

        parsed2 = parse_output(output, ['key1', 'key4', 'key7'])
        self.assertEqual('key1' in parsed2, True)
        self.assertEqual('key2' in parsed2, False)
        self.assertEqual('key4' in parsed2, True)
        self.assertEqual('key7' in parsed2, False)

    if is_win32:
        def test_script_env_win(self):
            r = get_script_env(self.env, 'testdata\\testvars.cmd', vars=['INCLUDE'])
            self.assertEqual(len(r), 1)
            self.assertEqual(r.get('INCLUDE', None),
                             r'C:\Program Files (x86)\joe\myinclude\INCLUDE;C:\foo\INCLUDE;oddvar;;;like this')

            r = get_script_env(self.env, os.path.join('testdata', 'testvars.cmd'), vars=['LIB'])
            self.assertEqual(len(r), 1)
            self.assertEqual(r.get('LIB', None), r'C:\Windows\someplace;C:\Program Files (x86)\joe\myinclude\LIB;C:\foo\lib;')

            r = get_script_env(self.env, os.path.join('testdata', 'testvars.cmd'), vars=['DUMMY'])
            self.assertEqual(len(r), 0)
            self.assertEqual(r.get('DUMMY', None), None)

            r = get_script_env(self.env, os.path.join('testdata', 'testvars.cmd'), args='dummy_arg1 dummy_arg2', vars=None)
            expectedOutput = {}
            expectedOutput['ARGTEST'] = r'dummy_arg1'
            expectedOutput['INCLUDE'] = r'C:\Program Files (x86)\joe\myinclude\INCLUDE;C:\foo\INCLUDE;oddvar;;;like this'
            expectedOutput['LIB'] = r'C:\Windows\someplace;C:\Program Files (x86)\joe\myinclude\LIB;C:\foo\lib;'
            expectedOutput['LIBPATH'] = r'C:\Windows\someplace;'
            for key in expectedOutput.keys():
                self.assertEqual(r[key], expectedOutput[key])
            self.assertEqual('DUMMY' in r, False)

        def test_merge_env_win(self):
            cenv = self.env.Clone()
            merge_script_vars(cenv, 'testdata\\testvars.cmd', vars=['INCLUDE'])
            # print cenv.Dump('ENV')
            self.assertEqual(cenv['ENV'].get('INCLUDE', None),
                             r'C:\Program Files (x86)\joe\myinclude\INCLUDE;C:\foo\INCLUDE;oddvar;like this')

            cenv = self.env.Clone()
            merge_script_vars(cenv, os.path.join('testdata', 'testvars.cmd'), vars=['LIB'])
            self.assertEqual(cenv['ENV'].get('LIB', None),
                             r'C:\Windows\someplace;C:\Program Files (x86)\joe\myinclude\LIB;C:\foo\lib')

            cenv = self.env.Clone()
            merge_script_vars(cenv, os.path.join('testdata', 'testvars.cmd'), args='dummy_arg1 dummy_arg2', vars=None)
            self.assertEqual(cenv['ENV'].get('ARGTEST', None), 'dummy_arg1')
            self.assertEqual(cenv['ENV'].get('INCLUDE', None),
                             r'C:\Program Files (x86)\joe\myinclude\INCLUDE;C:\foo\INCLUDE;oddvar;like this')
            self.assertEqual(cenv['ENV'].get('LIB', None),
                             r'C:\Windows\someplace;C:\Program Files (x86)\joe\myinclude\LIB;C:\foo\lib')
            self.assertEqual(cenv['ENV'].get('LIBPATH', None), r'C:\Windows\someplace')

    elif is_linux or is_darwin:
        def test_get_script_env(self):
            r = get_script_env(self.env, 'testdata/testvars.sh', vars=['INCLUDE'])
            self.assertEqual(len(r), 1)
            self.assertEqual(r.get('INCLUDE', None), r"'/usr/bin/joe/myinclude/INCLUDE:/opt/foo/INCLUDE:oddvar:::like this'")

            r = get_script_env(self.env, os.path.join('testdata', 'testvars.sh'), vars=['LIB'])
            self.assertEqual(len(r), 1)
            self.assertEqual(r.get('LIB', None), r'/opt/someplace:/usr/bin/joe/myinclude/LIB:/opt/foo/lib:')

            r = get_script_env(self.env, os.path.join('testdata', 'testvars.sh'), vars=['DUMMY'])
            self.assertEqual(len(r), 0)
            self.assertEqual(r.get('DUMMY', None), None)

            r = get_script_env(self.env, os.path.join('testdata', 'testvars.sh'), args='dummy_arg1 dummy_arg2', vars=None)
            expectedOutput = {}
            expectedOutput['ARGTEST'] = r'dummy_arg1'
            expectedOutput['INCLUDE'] = r"'/usr/bin/joe/myinclude/INCLUDE:/opt/foo/INCLUDE:oddvar:::like this'"
            expectedOutput['LIB'] = r'/opt/someplace:/usr/bin/joe/myinclude/LIB:/opt/foo/lib:'
            expectedOutput['LIBPATH'] = r'/opt/someplace:'
            for key in expectedOutput.keys():
                self.assertEqual(r[key], expectedOutput[key])
            self.assertEqual('DUMMY' in r, False)

        def test_merge_script_vars(self):
            cenv = self.env.Clone()
            merge_script_vars(cenv, 'testdata/testvars.sh', vars=['INCLUDE'])
            # print cenv.Dump('ENV')
            self.assertEqual(cenv['ENV'].get('INCLUDE', None),
                             r"'/usr/bin/joe/myinclude/INCLUDE:/opt/foo/INCLUDE:oddvar:like this'")

            cenv = self.env.Clone()
            merge_script_vars(cenv, os.path.join('testdata', 'testvars.sh'), vars=['LIB'])
            self.assertEqual(cenv['ENV'].get('LIB', None), r'/opt/someplace:/usr/bin/joe/myinclude/LIB:/opt/foo/lib')

            cenv = self.env.Clone()
            merge_script_vars(cenv, os.path.join('testdata', 'testvars.sh'), args='dummy_arg1 dummy_arg2', vars=None)
            self.assertEqual(cenv['ENV'].get('ARGTEST', None), 'dummy_arg1')
            self.assertEqual(cenv['ENV'].get('INCLUDE', None),
                             r"'/usr/bin/joe/myinclude/INCLUDE:/opt/foo/INCLUDE:oddvar:like this'")
            self.assertEqual(cenv['ENV'].get('LIB', None), r'/opt/someplace:/usr/bin/joe/myinclude/LIB:/opt/foo/lib')
            self.assertEqual(cenv['ENV'].get('LIBPATH', None), r'/opt/someplace')
