"""Tests for the optional build-command wrapper variables.

AUTO_MAKE_CONFIGURE_WRAPPER / AUTO_MAKE_MAKE_WRAPPER (automake) and
CMAKE_WRAPPER (cmake) let a toolchain wrap configure/make/cmake invocations
(e.g. emconfigure / emmake / emcmake). All default to empty, so they add
nothing to the command line unless set.
"""
import pytest

import parts.pieces.automake  # noqa: F401  registers AUTO_MAKE_*_WRAPPER
import parts.pieces.cmake  # noqa: F401  registers CMAKE_WRAPPER
import parts.settings as parts_settings


WRAPPER_VARS = ['AUTO_MAKE_CONFIGURE_WRAPPER', 'AUTO_MAKE_MAKE_WRAPPER', 'CMAKE_WRAPPER']


@pytest.fixture
def env():
    return parts_settings.DefaultSettings().Environment()


class TestWrapperDefaults:
    @pytest.mark.parametrize('var', WRAPPER_VARS)
    def test_default_empty(self, env, var):
        assert env.subst('$' + var) == ''


class TestWrapperApplied:
    def test_make_wrapper_empty_is_just_make(self, env):
        assert env.subst('$AUTO_MAKE_MAKE_WRAPPER make').split() == ['make']

    def test_make_wrapper_set_prefixes_make(self, env):
        env['AUTO_MAKE_MAKE_WRAPPER'] = 'emmake'
        assert env.subst('$AUTO_MAKE_MAKE_WRAPPER make').split() == ['emmake', 'make']

    def test_configure_wrapper_set_prefixes_configure(self, env):
        env['AUTO_MAKE_CONFIGURE_WRAPPER'] = 'emconfigure'
        assert env.subst('$AUTO_MAKE_CONFIGURE_WRAPPER ./configure').split() == ['emconfigure', './configure']

    def test_cmake_wrapper_empty_is_just_cmake(self, env):
        env['CMAKE'] = 'cmake'
        assert env.subst('$CMAKE_WRAPPER $CMAKE').split() == ['cmake']

    def test_cmake_wrapper_set_prefixes_cmake(self, env):
        env['CMAKE'] = 'cmake'
        env['CMAKE_WRAPPER'] = 'emcmake'
        assert env.subst('$CMAKE_WRAPPER $CMAKE').split() == ['emcmake', 'cmake']
