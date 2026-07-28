"""Tests for CMake configure/build flag wiring.

Covers the non-tool CMake configurability: the newly registered
CMAKE_BUILD_TYPE / CMAKE_GENERATOR / CMAKE_BUILDSUBDIR variables, and that
user flags ($CFLAGS/$CXXFLAGS), install subdirs, build type and generator
flow through the cmake configure arguments via substitution. These check the
wiring without invoking cmake itself.
"""
import pytest

import parts.pieces.cmake  # noqa: F401  registers the CMAKE_* variables
import parts.settings as parts_settings


@pytest.fixture
def env():
    return parts_settings.DefaultSettings().Environment()


class TestCMakeRegisteredVars:
    @pytest.mark.parametrize('var,default', [
        ('CMAKE_BUILD_TYPE', 'Release'),
        ('CMAKE_GENERATOR', ''),
        ('CMAKE_BUILDSUBDIR', 'build'),
    ])
    def test_registered_default(self, env, var, default):
        assert env.subst('$' + var) == default

    def test_builddir_uses_buildsubdir(self, env):
        env['CMAKE_BUILDSUBDIR'] = 'cmbuild'
        assert env.subst('$CMAKE_BUILDDIR').endswith('/cmbuild')


class TestCMakeFlagFlowThrough:
    # the exact -D fragments the CMake() configure args are built from
    LIBDIR = '-DCMAKE_INSTALL_LIBDIR:PATH=$INSTALL_LIB_SUBDIR'
    CXX = '-DCMAKE_CXX_FLAGS="$CCFLAGS $CXXFLAGS"'
    CC = '-DCMAKE_C_FLAGS="$CCFLAGS $CFLAGS"'
    GEN = '${define_if("$CMAKE_GENERATOR","-DCMAKE_GENERATOR=$CMAKE_GENERATOR")}'

    def test_cxxflags_and_cflags_reach_args(self, env):
        env['CXXFLAGS'] = '-std=c++20'
        env['CFLAGS'] = '-std=c11'
        assert '-std=c++20' in env.subst(self.CXX)
        assert '-std=c11' in env.subst(self.CC)

    def test_install_libdir_is_configurable(self, env):
        env['INSTALL_LIB_SUBDIR'] = 'lib64'
        assert env.subst(self.LIBDIR) == '-DCMAKE_INSTALL_LIBDIR:PATH=lib64'

    def test_generator_emitted_only_when_set(self, env):
        # default empty -> no -DCMAKE_GENERATOR at all
        assert env.subst(self.GEN).strip() == ''
        env['CMAKE_GENERATOR'] = 'Ninja'
        assert env.subst(self.GEN).strip() == '-DCMAKE_GENERATOR=Ninja'

    def test_build_type_is_configurable(self, env):
        env['CMAKE_BUILD_TYPE'] = 'Debug'
        assert env.subst('--config $CMAKE_BUILD_TYPE') == '--config Debug'
