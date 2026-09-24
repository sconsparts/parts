"""Tests for the optional compiler-launcher variables CC_LAUNCHER / CXX_LAUNCHER.

A toolchain or site can set these to a launcher such as ccache or sccache; they
are prefixed to the *compiler* invocation across all three build surfaces:

  * native SCons compiles  -> $CC_LAUNCHER/$CXX_LAUNCHER lead the C*COM strings
    (tools/cc.py, tools/c++.py);
  * CMake  -> routed via -DCMAKE_<LANG>_COMPILER_LAUNCHER (pieces/cmake.py), so
    CMAKE_<LANG>_COMPILER stays a clean path and the compiler probe is unaffected;
  * AutoMake -> folded into CC=/CXX= passed to configure (pieces/automake.py),
    since autotools has no launcher concept.

Both default to empty, so they add nothing to any command line unless set.
These tests pin the defaults and the native C*COM wiring. The CMake and
AutoMake paths are covered by the compiler_launcher gold tests, which build
through a logging launcher.
"""
import os

import pytest
import SCons.Action

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

    @pytest.mark.parametrize('com,prefix', [
        ('CCCOM', '$( $CC_LAUNCHER $) ${TEMPFILE("$CC '),
        ('SHCCCOM', '$( $CC_LAUNCHER $) ${TEMPFILE("$SHCC '),
        ('CXXCOM', '$( $CXX_LAUNCHER $) ${TEMPFILE("$CXX '),
        ('SHCXXCOM', '$( $CXX_LAUNCHER $) ${TEMPFILE("$SHCXX '),
    ])
    def test_launcher_leads_compiler_outside_tempfile(self, env, com, prefix):
        # the launcher goes in front of TEMPFILE, not inside it: a response file
        # keeps only the first word of the command on the command line, so a
        # launcher inside it would run with just @file and no compiler
        assert env[com].startswith(prefix)


OLD_CCCOM = '${TEMPFILE("$CC -o $TARGET -c $CFLAGS $CCFLAGS $_CCCOMCOM $SOURCES $CCARCHFLAGS","$CCCOMSTR")}'


def _nodes(env, src):
    return [env.File('x.o')], [env.File(src)]


def _command(env, com, src='x.c'):
    target, source = _nodes(env, src)
    return env.subst('$' + com, target=target, source=source).split()


def _signature(env, com, src='x.c'):
    target, source = _nodes(env, src)
    return SCons.Action.Action(com).get_contents(target, source, env)


class TestNativeApplied:
    @pytest.mark.parametrize('com,var,src', [
        ('CCCOM', 'CC_LAUNCHER', 'x.c'),
        ('SHCCCOM', 'CC_LAUNCHER', 'x.c'),
        ('CXXCOM', 'CXX_LAUNCHER', 'x.cpp'),
        ('SHCXXCOM', 'CXX_LAUNCHER', 'x.cpp'),
    ])
    def test_set_launcher_leads_the_compile(self, env, com, var, src):
        env[var] = 'ccache --tag x'
        assert _command(env, com, src)[:3] == ['ccache', '--tag', 'x']

    def test_empty_launcher_leaves_the_compiler_first(self, env):
        assert _command(env, 'CCCOM')[0] == env.subst('$CC')
        assert _command(env, 'CXXCOM', 'x.cpp')[0] == env.subst('$CXX')

    def test_signature_without_a_launcher_is_unchanged(self, env):
        # an existing tree must not recompile after the upgrade
        assert _signature(env, '$CCCOM') == _signature(env, OLD_CCCOM)

    def test_launcher_is_not_in_the_signature(self, env):
        # turning ccache on or off must not recompile the tree
        plain = _signature(env, '$CCCOM')
        env['CC_LAUNCHER'] = 'ccache'
        assert _signature(env, '$CCCOM') == plain

    def test_compiler_stays_the_implicit_dependency(self, env):
        # SCons makes the first word of a command an implicit dependency, which
        # has to be the compiler, so updating it in place still recompiles
        target, source = _nodes(env, 'x.c')
        compiler = env.WhereIs(env.subst('$CC'))
        if not compiler:
            pytest.skip('no C compiler on PATH')
        env['CC_LAUNCHER'] = env.WhereIs('sh')
        deps = SCons.Action.Action('$CCCOM').get_implicit_deps(target, source, env)
        assert [str(d) for d in deps] == [str(env.File(compiler))]
