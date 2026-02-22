"""Tests for merge_script module.

Validates extraction of environment variables from shell scripts (.cmd on Windows, 
.sh on Unix). Tests cover normalization of environment dictionaries, execution of 
shell scripts with argument passing, parsing of shell output into key-value pairs, 
and merging of extracted variables into SCons environments.
"""
import SCons.Script
from parts.pieces.merge_script import *
import sys
import os
import copy
import pytest

is_win32 = False
is_linux = False
is_darwin = False
if sys.platform == 'win32':
    is_win32 = True
elif sys.platform.startswith('linux'):
    is_linux = True
elif sys.platform == 'darwin':
    is_darwin = True

# Test data paths
TESTDATA_DIR = os.path.join('./tests/unit/testdata')
TESTVARS_CMD = os.path.join(TESTDATA_DIR, 'testvars.cmd')
TESTVARS_SH = os.path.join(TESTDATA_DIR, 'testvars.sh')


def assert_contains(output, expected_text):
    """Assert that output contains expected_text."""
    assert expected_text in output


@pytest.fixture
def scons_env():
    """Provide a clean SCons environment for each test."""
    return SCons.Script.Environment(tools=[])


class TestMergeScript:
    """Test suite for merge_script environment extraction functionality."""

    def test_normalize_env(self, scons_env):
        """Test normalize_env handles platform-specific encoding correctly.
        
        Validates that normalize_env returns bytes on Windows (for subprocess compatibility)
        and strings on Unix platforms. Verifies that non-existent keys return None.
        """
        newEnv = {}
        newEnv['MYENV'] = 'MYVALUE'

        osEnvCopy = copy.deepcopy(os.environ)
        for key in newEnv.keys():
            os.environ[key] = newEnv[key]
        keys = list(newEnv.keys())
        keys.append('DUMMY')
        norm_env = normalize_env(scons_env['ENV'], keys)
        os.environ = osEnvCopy

        for key in newEnv.keys():
            actual_value = norm_env.get(key, None)
            expected_value = newEnv[key]
            # On Windows, normalize_env intentionally returns bytes for subprocess compatibility
            if is_win32:
                expected_value = expected_value.encode('mbcs')
            assert actual_value == expected_value
        assert norm_env.get('DUMMY', None) is None

    @pytest.mark.skipif(not is_win32, reason='Windows only')
    def test_get_output_windows(self, scons_env):
        """Test get_output executes Windows batch files and captures output.
        
        Validates that shell script execution returns output containing expected
        environment variable assignments and command-line arguments.
        """
        norm_env = normalize_env(scons_env['ENV'])
        output = get_output(TESTVARS_CMD,
                            args='dummy_arg1 dummy_arg2', shellenv=norm_env)
        expectedOutput = []
        expectedOutput.append(r'ARGTEST=dummy_arg1')
        expectedOutput.append(r'INCLUDE=C:\Program Files (x86)\joe\myinclude\INCLUDE;C:\foo\INCLUDE;oddvar;;;like this')
        expectedOutput.append(r'LIB=C:\Windows\someplace;C:\Program Files (x86)\joe\myinclude\LIB;C:\foo\lib;')
        expectedOutput.append(r'LIBPATH=C:\Windows\someplace;')
        for expectedOutputItem in expectedOutput:
            assert_contains(output, expectedOutputItem)

    @pytest.mark.skipif(not (is_linux or is_darwin), reason='Unix only')
    def test_get_output_unix(self, scons_env):
        """Test get_output executes Unix shell scripts and captures output.
        
        Validates that shell script execution returns output containing expected
        environment variable assignments and command-line arguments on Unix platforms.
        """
        output = get_output(TESTVARS_SH,
                            args='dummy_arg1 dummy_arg2', shellenv=scons_env['ENV'])
        expectedOutput = []
        expectedOutput.append(r"INCLUDE='/usr/bin/joe/myinclude/INCLUDE:/opt/foo/INCLUDE:oddvar:::like this'")
        expectedOutput.append(r'LIB=/opt/someplace:/usr/bin/joe/myinclude/LIB:/opt/foo/lib:')
        expectedOutput.append(r'LIBPATH=/opt/someplace:')
        for expectedOutputItem in expectedOutput:
            assert_contains(output, expectedOutputItem)

    def test_parse_output(self, scons_env):
        """Test parse_output correctly parses key=value formatted shell output.
        
        Validates parsing of well-formed key=value pairs, preservation of spacing in
        values, handling of empty values, rejection of malformed entries, and filtering
        by key list when provided.
        """
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
        assert parsed1['key1'] == 'var1'
        assert parsed1['key2'] == ' var2 var22'
        assert parsed1['key3'] == ''
        assert parsed1['key4'] == ' var4'
        assert 'key5' not in parsed1
        assert 'key6' not in parsed1
        assert 'key7' not in parsed1
        assert 'key8' not in parsed1

        parsed2 = parse_output(output, ['key1', 'key4', 'key7'])
        assert 'key1' in parsed2
        assert 'key2' not in parsed2
        assert 'key4' in parsed2
        assert 'key7' not in parsed2

    @pytest.mark.skipif(not is_win32, reason='Windows only')
    def test_script_env_win(self, scons_env):
        """Test get_script_env extracts variables from Windows batch files.
        
        Validates filtering by specific variable name, presence of non-existent variables,
        extraction of all variables when filter is None, and argument passing to scripts.
        """
        r = get_script_env(scons_env, TESTVARS_CMD, vars=['INCLUDE'])
        assert 'INCLUDE' in r
        assert r.get('INCLUDE', None) == r'C:\Program Files (x86)\joe\myinclude\INCLUDE;C:\foo\INCLUDE;oddvar;;;like this'

        r = get_script_env(scons_env, TESTVARS_CMD, vars=['LIB'])
        assert 'LIB' in r
        assert r.get('LIB', None) == r'C:\Windows\someplace;C:\Program Files (x86)\joe\myinclude\LIB;C:\foo\lib;'

        r = get_script_env(scons_env, TESTVARS_CMD, vars=['DUMMY'])
        assert 'DUMMY' not in r

        r = get_script_env(scons_env, TESTVARS_CMD,
                           args='dummy_arg1 dummy_arg2', vars=None)
        expectedOutput = {}
        expectedOutput['ARGTEST'] = r'dummy_arg1'
        expectedOutput['INCLUDE'] = r'C:\Program Files (x86)\joe\myinclude\INCLUDE;C:\foo\INCLUDE;oddvar;;;like this'
        expectedOutput['LIB'] = r'C:\Windows\someplace;C:\Program Files (x86)\joe\myinclude\LIB;C:\foo\lib;'
        expectedOutput['LIBPATH'] = r'C:\Windows\someplace;'
        for key in expectedOutput.keys():
            assert r[key] == expectedOutput[key]
        assert 'DUMMY' not in r

    @pytest.mark.skipif(not is_win32, reason='Windows only')
    def test_merge_env_win(self, scons_env):
        """Test merge_script_vars integrates extracted Windows script variables into SCons env.
        
        Validates filtering by specific variable name, extraction with arguments, and
        extraction of all variables when filter is None. Verifies merged values appear
        in the cloned environment's ENV dict.
        """
        cenv = scons_env.Clone()
        merge_script_vars(cenv, TESTVARS_CMD, vars=['INCLUDE'])
        assert cenv['ENV'].get('INCLUDE', None) == r'C:\Program Files (x86)\joe\myinclude\INCLUDE;C:\foo\INCLUDE;oddvar;like this'

        cenv = scons_env.Clone()
        merge_script_vars(cenv, TESTVARS_CMD, vars=['LIB'])
        assert cenv['ENV'].get('LIB', None) == r'C:\Windows\someplace;C:\Program Files (x86)\joe\myinclude\LIB;C:\foo\lib'

        cenv = scons_env.Clone()
        merge_script_vars(cenv, TESTVARS_CMD, args='dummy_arg1 dummy_arg2', vars=None)
        assert cenv['ENV'].get('ARGTEST', None) == 'dummy_arg1'
        assert cenv['ENV'].get('INCLUDE', None) == r'C:\Program Files (x86)\joe\myinclude\INCLUDE;C:\foo\INCLUDE;oddvar;like this'
        assert cenv['ENV'].get('LIB', None) == r'C:\Windows\someplace;C:\Program Files (x86)\joe\myinclude\LIB;C:\foo\lib'
        assert cenv['ENV'].get('LIBPATH', None) == r'C:\Windows\someplace'

    @pytest.mark.skipif(not (is_linux or is_darwin), reason='Unix only')
    def test_get_script_env(self, scons_env):
        """Test get_script_env extracts variables from Unix shell scripts.
        
        Validates filtering by specific variable name, presence of non-existent variables,
        extraction of all variables when filter is None, and argument passing to scripts
        on Unix platforms.
        """
        r = get_script_env(scons_env, TESTVARS_SH, vars=['INCLUDE'])
        assert len(r) == 1
        assert r.get('INCLUDE', None) == r"'/usr/bin/joe/myinclude/INCLUDE:/opt/foo/INCLUDE:oddvar:::like this'"

        r = get_script_env(scons_env, TESTVARS_SH, vars=['LIB'])
        assert len(r) == 1
        assert r.get('LIB', None) == r'/opt/someplace:/usr/bin/joe/myinclude/LIB:/opt/foo/lib:'

        r = get_script_env(scons_env, TESTVARS_SH, vars=['DUMMY'])
        assert len(r) == 0
        assert r.get('DUMMY', None) is None

        r = get_script_env(scons_env, TESTVARS_SH,
                           args='dummy_arg1 dummy_arg2', vars=None)
        expectedOutput = {}
        expectedOutput['ARGTEST'] = r'dummy_arg1'
        expectedOutput['INCLUDE'] = r"'/usr/bin/joe/myinclude/INCLUDE:/opt/foo/INCLUDE:oddvar:::like this'"
        expectedOutput['LIB'] = r'/opt/someplace:/usr/bin/joe/myinclude/LIB:/opt/foo/lib:'
        expectedOutput['LIBPATH'] = r'/opt/someplace:'
        for key in expectedOutput.keys():
            assert r[key] == expectedOutput[key]
        assert 'DUMMY' not in r

    @pytest.mark.skipif(not (is_linux or is_darwin), reason='Unix only')
    def test_merge_script_vars(self, scons_env):
        """Test merge_script_vars integrates extracted Unix script variables into SCons env.
        
        Validates filtering by specific variable name, extraction with arguments, and
        extraction of all variables when filter is None. Verifies merged values appear
        in the cloned environment's ENV dict on Unix platforms.
        """
        cenv = scons_env.Clone()
        merge_script_vars(cenv, TESTVARS_SH, vars=['INCLUDE'])
        assert cenv['ENV'].get('INCLUDE', None) == r"'/usr/bin/joe/myinclude/INCLUDE:/opt/foo/INCLUDE:oddvar:like this'"

        cenv = scons_env.Clone()
        merge_script_vars(cenv, TESTVARS_SH, vars=['LIB'])
        assert cenv['ENV'].get('LIB', None) == r'/opt/someplace:/usr/bin/joe/myinclude/LIB:/opt/foo/lib'

        cenv = scons_env.Clone()
        merge_script_vars(cenv, TESTVARS_SH, args='dummy_arg1 dummy_arg2', vars=None)
        assert cenv['ENV'].get('ARGTEST', None) == 'dummy_arg1'
        assert cenv['ENV'].get('INCLUDE', None) == r"'/usr/bin/joe/myinclude/INCLUDE:/opt/foo/INCLUDE:oddvar:like this'"
        assert cenv['ENV'].get('LIB', None) == r'/opt/someplace:/usr/bin/joe/myinclude/LIB:/opt/foo/lib'
        assert cenv['ENV'].get('LIBPATH', None) == r'/opt/someplace'
