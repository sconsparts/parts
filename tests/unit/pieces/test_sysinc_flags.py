"""Tests for SYSINCPREFIX/SYSINCSUFFIX wiring across cc, c++, automake, and cmake.

Covers the variables introduced so that a Part can route its CPPPATH entries
through a separate prefix/suffix pair (e.g. ``-isystem``) without changing the
defaults for parts that don't opt in.
"""
import os
import platform

import pytest
import SCons.Script

# Importing the pieces modules triggers their api.register.add_variable() calls
# (AUTO_MAKE_INCLUDE_FLAGS, _ABSCPPINCFLAGS, _ABSCPPSYSINCFLAGS, CMAKE_INCLUDE_FLAG,
# CMAKE_INCLUDE_SYSTEM_FLAG, ...). Without the imports the variables wouldn't be
# registered against DefaultSettings.
import parts.pieces.automake  # noqa: F401
import parts.pieces.cmake  # noqa: F401
import parts.settings as parts_settings


# Toolpath points at the in-tree Parts tools so the c++/cc modules under test get
# picked up rather than the stock SCons ones.
PARTS_TOOLS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src', 'parts', 'tools')
)


# toolchain=[] gives a compiler-less env, so these fixtures observe the generic
# c++/cc tool defaults (SYSINCPREFIX=$INCPREFIX) in isolation rather than the
# platform compiler's settings. gcc/clang override SYSINCPREFIX to -isystem (see
# test_system_includes.py); that override is deliberately out of scope here.
@pytest.fixture
def env_cxx():
    env = parts_settings.DefaultSettings().Environment(toolchain=[])
    env.Tool('c++', toolpath=[PARTS_TOOLS])
    return env


@pytest.fixture
def env_cc():
    env = parts_settings.DefaultSettings().Environment(toolchain=[])
    env.Tool('cc', toolpath=[PARTS_TOOLS])
    return env


class TestSysIncToolDefaults:
    """The cc and c++ tools must define SYSINCPREFIX/SYSINCSUFFIX defaulting to
    INCPREFIX/INCSUFFIX so existing parts see identical command lines."""

    def test_cxx_defines_sysincprefix(self, env_cxx):
        assert env_cxx['SYSINCPREFIX'] == '$INCPREFIX'
        assert env_cxx['SYSINCSUFFIX'] == '$INCSUFFIX'

    def test_cc_defines_sysincprefix(self, env_cc):
        assert env_cc['SYSINCPREFIX'] == '$INCPREFIX'
        assert env_cc['SYSINCSUFFIX'] == '$INCSUFFIX'

    def test_default_expansion_matches_incprefix(self, env_cxx):
        assert env_cxx.subst('$SYSINCPREFIX') == env_cxx.subst('$INCPREFIX')
        assert env_cxx.subst('$SYSINCSUFFIX') == env_cxx.subst('$INCSUFFIX')


class TestAbsCppSysIncFlagsExpansion:
    """_ABSCPPSYSINCFLAGS expands CPPPATH through SYSINCPREFIX/SYSINCSUFFIX."""

    def test_default_matches_abscppincflags(self, env_cxx):
        env_cxx['CPPPATH'] = ['/usr/local/include/foo', '/opt/bar/include']
        assert env_cxx.subst('$_ABSCPPSYSINCFLAGS') == env_cxx.subst('$_ABSCPPINCFLAGS')

    def test_isystem_override_appears_in_expansion(self, env_cxx):
        env_cxx['SYSINCPREFIX'] = '-isystem '
        env_cxx['SYSINCSUFFIX'] = ''
        env_cxx['CPPPATH'] = ['/usr/local/include/foo', '/opt/bar/include']
        expanded = env_cxx.subst('$_ABSCPPSYSINCFLAGS')
        assert expanded.count('-isystem') == 2
        # The bare -I from INCPREFIX must not leak through when using the
        # SYSINC expansion.
        assert '-I/' not in expanded
        assert 'foo' in expanded and 'bar' in expanded

    def test_abscppincflags_unaffected_by_sysincprefix(self, env_cxx):
        """Regression guard: overriding SYSINCPREFIX must not change _ABSCPPINCFLAGS."""
        env_cxx['CPPPATH'] = ['/usr/local/include/foo']
        baseline = env_cxx.subst('$_ABSCPPINCFLAGS')
        env_cxx['SYSINCPREFIX'] = '-isystem '
        assert env_cxx.subst('$_ABSCPPINCFLAGS') == baseline


class TestAutoMakeIncludeFlagsHook:
    """AUTO_MAKE_INCLUDE_FLAGS lets a part swap CPPPATH onto -isystem without
    rewriting the AutoMake configure command line."""

    def test_default_is_abscppincflags(self, env_cxx):
        assert env_cxx['AUTO_MAKE_INCLUDE_FLAGS'] == '$_ABSCPPINCFLAGS'

    def test_override_to_system_includes(self, env_cxx):
        env_cxx['SYSINCPREFIX'] = '-isystem '
        env_cxx['AUTO_MAKE_INCLUDE_FLAGS'] = '$_ABSCPPSYSINCFLAGS'
        env_cxx['CPPPATH'] = ['/usr/local/include/foo']
        expanded = env_cxx.subst('$AUTO_MAKE_INCLUDE_FLAGS')
        assert '-isystem' in expanded
        assert '-I/' not in expanded


class TestCMakeIncludeFlagVariables:
    """CMAKE_INCLUDE_FLAG and CMAKE_INCLUDE_SYSTEM_FLAG forward INCPREFIX and
    SYSINCPREFIX into the cmake configure invocation, letting users override
    one without disturbing the other."""

    def test_cmake_include_flag_default(self, env_cxx):
        assert env_cxx['CMAKE_INCLUDE_FLAG'] == '$INCPREFIX'
        expected = '/I' if platform.system() == 'Windows' else '-I'
        assert env_cxx.subst('$CMAKE_INCLUDE_FLAG') == expected

    def test_cmake_include_system_flag_default(self, env_cxx):
        assert env_cxx['CMAKE_INCLUDE_SYSTEM_FLAG'] == '$SYSINCPREFIX'
        # SYSINCPREFIX defaults to $INCPREFIX which is '-I' (or '/I' on Windows)
        expected = '/I' if platform.system() == 'Windows' else '-I'
        assert env_cxx.subst('$CMAKE_INCLUDE_SYSTEM_FLAG') == expected

    def test_cmake_include_system_flag_follows_sysincprefix(self, env_cxx):
        env_cxx['SYSINCPREFIX'] = '-isystem '
        assert env_cxx.subst('$CMAKE_INCLUDE_SYSTEM_FLAG').strip() == '-isystem'

    def test_cmake_include_flag_does_not_follow_sysincprefix(self, env_cxx):
        """Regression guard: CMAKE_INCLUDE_FLAG (the non-system one) must keep
        tracking INCPREFIX even if a user overrides SYSINCPREFIX."""
        env_cxx['SYSINCPREFIX'] = '-isystem '
        expected = '/I' if platform.system() == 'Windows' else '-I'
        assert env_cxx.subst('$CMAKE_INCLUDE_FLAG') == expected
