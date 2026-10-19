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
These tests pin the defaults, the native C*COM wiring, and the configure
arguments AutoMake() and CMake() build from a launcher. The compiler_launcher
gold tests build all three paths through a logging launcher.
"""
import os
import shlex

import pytest
import SCons.Action

import parts.pieces.automake as automake_piece
import parts.pieces.cmake as cmake_piece
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


def _as_run(env, arg):
    # what the shell receives: SCons expands the command, then sh splits it
    return shlex.split(env.subst(arg))


class TestConfigureArguments:
    """The launcher arguments AutoMake() and CMake() add to their configure step."""

    def test_automake_without_a_launcher_is_unchanged(self, env):
        # exactly what the configure command always had, so no part reconfigures
        assert automake_piece.compiler_assignment(env, 'CC', 'CC_LAUNCHER') == 'CC="$CC"'
        assert automake_piece.compiler_assignment(env, 'CXX', 'CXX_LAUNCHER') == 'CXX="$CXX"'

    def test_automake_launcher_without_a_compiler_is_unchanged(self, env):
        # with no C++ compiler, configure finds one itself, as before; it must
        # not get the launcher alone as the compiler
        env['CXX'] = ''
        env['CXX_LAUNCHER'] = 'ccache'
        assert automake_piece.compiler_assignment(env, 'CXX', 'CXX_LAUNCHER') == 'CXX="$CXX"'

    # configure splits CC at whitespace and does not remove quotes, so the
    # quoted words with spaces in the next two tests fail its compiler probes
    # (see compiler_assignment). They pin only that the argument stays one
    # shell word: quotes in it do not end it early and spill the rest into
    # other configure arguments.
    def test_automake_launcher_quotes_stay_in_one_argument(self, env):
        env['CC_LAUNCHER'] = 'env CCACHE_DIR="two words" ccache'
        arg = automake_piece.compiler_assignment(env, 'CC', 'CC_LAUNCHER')
        assert _as_run(env, arg) == [f'CC=env CCACHE_DIR="two words" ccache {env.subst("$CC")}']

    def test_automake_compiler_quotes_stay_in_one_argument(self, env):
        env['CC'] = "gcc -DX='a b'"
        env['CC_LAUNCHER'] = 'ccache'
        arg = automake_piece.compiler_assignment(env, 'CC', 'CC_LAUNCHER')
        assert _as_run(env, arg) == ["CC=ccache gcc -DX='a b'"]

    def test_automake_launcher_dollar_is_expanded_once(self, env):
        # $$ is a literal $ in a construction variable, here as anywhere
        env['CC_LAUNCHER'] = 'env CCACHE_DIR=$$CC ccache'
        arg = automake_piece.compiler_assignment(env, 'CC', 'CC_LAUNCHER')
        assert _as_run(env, arg) == [f'CC=env CCACHE_DIR=$CC ccache {env.subst("$CC")}']

    def test_cmake_without_a_launcher_adds_nothing(self, env):
        assert cmake_piece.launcher_definition(env, 'C', 'CC_LAUNCHER') == ''
        assert cmake_piece.launcher_definition(env, 'CXX', 'CXX_LAUNCHER') == ''

    def test_cmake_launcher_is_one_list_argument(self, env):
        env['CC_LAUNCHER'] = 'env \'CCACHE_DIR=two "quoted" words\' ccache'
        arg = cmake_piece.launcher_definition(env, 'C', 'CC_LAUNCHER')
        # one shell word holding CMake's ;-list, a word's double quotes intact
        assert _as_run(env, arg) == ['-DCMAKE_C_COMPILER_LAUNCHER=env;CCACHE_DIR=two "quoted" words;ccache']

    def test_cmake_launcher_semicolon_stays_in_its_word(self, env):
        env['CC_LAUNCHER'] = "env 'CCACHE_DIR=/cache/a;b' ccache"
        arg = cmake_piece.launcher_definition(env, 'C', 'CC_LAUNCHER')
        # CMake reads \; as a ; in the word, not as a list separator
        assert _as_run(env, arg) == [r'-DCMAKE_C_COMPILER_LAUNCHER=env;CCACHE_DIR=/cache/a\;b;ccache']

    def test_cmake_launcher_that_does_not_split_is_reported(self, env, monkeypatch):
        reported = []

        def fake_error_msg(msg, **kw):
            reported.append(msg)
            raise RuntimeError('reported')

        monkeypatch.setattr(cmake_piece.api.output, 'error_msg', fake_error_msg)
        env['CC_LAUNCHER'] = "ccache --opt=it's"
        with pytest.raises(RuntimeError):
            cmake_piece.launcher_definition(env, 'C', 'CC_LAUNCHER')
        assert 'CC_LAUNCHER' in reported[0] and "it's" in reported[0]

    def test_cmake_launcher_dollar_is_expanded_once(self, env):
        env['CC_LAUNCHER'] = 'env CCACHE_DIR=$$CC ccache'
        arg = cmake_piece.launcher_definition(env, 'C', 'CC_LAUNCHER')
        assert _as_run(env, arg) == ['-DCMAKE_C_COMPILER_LAUNCHER=env;CCACHE_DIR=$CC;ccache']
