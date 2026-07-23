"""Tests for the optional compiler-launcher variables CC_LAUNCHER / CXX_LAUNCHER.

A toolchain or site can set these to a launcher such as ccache or sccache; they
are prefixed to the *compiler* invocation across all three build surfaces:

  * native SCons compiles  -> $CC_LAUNCHER/$CXX_LAUNCHER lead the C*COM strings
    (tools/cc.py, tools/c++.py);
  * CMake  -> routed via -DCMAKE_<LANG>_COMPILER_LAUNCHER (pieces/cmake.py), so
    CMAKE_<LANG>_COMPILER stays a clean path and the compiler probe is unaffected;
  * AutoMake -> folded into CC=/CXX= passed to configure (pieces/automake.py),
    since autotools has no launcher concept.

Both default to empty, so they add nothing to any command line unless set. The
real cached-compile behavior with an actual ccache is out of scope here; this
just pins the wiring and the empty-default no-op.
"""
import os

import pytest

import parts.settings as parts_settings


PARTS_TOOLS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'parts', 'tools')
)


@pytest.fixture
def env():
    # toolchain=[] -> compiler-less base env, then apply the generic cc/c++ tools
    # from the working tree so we exercise their generate() defaults (where the
    # launcher vars and C*COM strings are set), not a platform compiler override.
    env = parts_settings.DefaultSettings().Environment(toolchain=[])
    env.Tool('cc', toolpath=[PARTS_TOOLS])
    env.Tool('c++', toolpath=[PARTS_TOOLS])
    return env


class TestDefaults:
    def test_launchers_default_empty(self, env):
        assert env['CC_LAUNCHER'] == ''
        assert env['CXX_LAUNCHER'] == ''

    @pytest.mark.parametrize('com,fragment', [
        ('CCCOM', '$CC_LAUNCHER $CC'),
        ('SHCCCOM', '$CC_LAUNCHER $SHCC'),
        ('CXXCOM', '$CXX_LAUNCHER $CXX'),
        ('SHCXXCOM', '$CXX_LAUNCHER $SHCXX'),
    ])
    def test_launcher_leads_compiler_in_com(self, env, com, fragment):
        # the launcher must sit immediately before the compiler token, so an empty
        # launcher is a clean no-op and a set one prefixes the compile
        assert fragment in env[com]


class TestNativeApplied:
    def test_empty_cc_launcher_is_noop(self, env):
        # empty launcher -> the compile command is just the bare compiler
        assert env.subst('$CC_LAUNCHER $CC').split() == env.subst('$CC').split()
        assert env.subst('$CXX_LAUNCHER $CXX').split() == env.subst('$CXX').split()

    def test_set_cc_launcher_prefixes_compiler(self, env):
        env['CC_LAUNCHER'] = 'ccache'
        tokens = env.subst('$CC_LAUNCHER $CC').split()
        assert tokens[0] == 'ccache'
        assert tokens[1:] == env.subst('$CC').split()

    def test_set_cxx_launcher_prefixes_compiler(self, env):
        env['CXX_LAUNCHER'] = 'sccache'
        tokens = env.subst('$CXX_LAUNCHER $CXX').split()
        assert tokens[0] == 'sccache'
        assert tokens[1:] == env.subst('$CXX').split()

    def test_shared_variants_honor_launcher(self, env):
        env['CC_LAUNCHER'] = 'ccache'
        env['CXX_LAUNCHER'] = 'ccache'
        assert env.subst('$CC_LAUNCHER $SHCC').split()[0] == 'ccache'
        assert env.subst('$CXX_LAUNCHER $SHCXX').split()[0] == 'ccache'


# The exact fragments as composed in pieces/cmake.py and pieces/automake.py.
CMAKE_C_FRAG = '${define_if("$CC_LAUNCHER","-DCMAKE_C_COMPILER_LAUNCHER=")}$CC_LAUNCHER'
CMAKE_CXX_FRAG = '${define_if("$CXX_LAUNCHER","-DCMAKE_CXX_COMPILER_LAUNCHER=")}$CXX_LAUNCHER'
AUTOMAKE_FRAG = 'CC="$CC_LAUNCHER $CC" CXX="$CXX_LAUNCHER $CXX"'


class TestCMakeArgs:
    def test_empty_emits_no_launcher_flag(self, env):
        assert env.subst(CMAKE_C_FRAG).strip() == ''
        assert env.subst(CMAKE_CXX_FRAG).strip() == ''

    def test_set_emits_compiler_launcher_flag(self, env):
        env['CC_LAUNCHER'] = 'ccache'
        env['CXX_LAUNCHER'] = 'ccache'
        assert env.subst(CMAKE_C_FRAG).strip() == '-DCMAKE_C_COMPILER_LAUNCHER=ccache'
        assert env.subst(CMAKE_CXX_FRAG).strip() == '-DCMAKE_CXX_COMPILER_LAUNCHER=ccache'

    def test_compiler_id_arg_stays_clean(self, env):
        # the launcher must NOT leak into CMAKE_*_COMPILER (would break the probe)
        env['CC_LAUNCHER'] = 'ccache'
        assert env.subst('-DCMAKE_C_COMPILER=$CC') == '-DCMAKE_C_COMPILER=' + env.subst('$CC')


class TestAutoMakeArgs:
    def test_empty_launcher_leaves_compiler_bare(self, env):
        # CC=" cc" word-splits to just the compiler; configure handles it
        out = env.subst(AUTOMAKE_FRAG)
        assert 'ccache' not in out and 'sccache' not in out
        assert 'CC="' in out and 'CXX="' in out

    def test_set_launcher_folds_into_cc(self, env):
        env['CC_LAUNCHER'] = 'ccache'
        env['CXX_LAUNCHER'] = 'ccache'
        out = env.subst(AUTOMAKE_FRAG)
        assert 'CC="ccache ' in out
        assert 'CXX="ccache ' in out
