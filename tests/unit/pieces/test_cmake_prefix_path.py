"""Tests for CMAKE_PREFIX_PATH propagation into the cmake configure step.

SdkCMakeConfig exports the SDK cmake-config dir as the public CMAKE_PREFIX_PATH
requirement, and the cmake configure command passes it to cmake as the
CMAKE_PREFIX_PATH environment variable (which find_package honors), mirroring
how PKG_CONFIG_PATH is handled. The critical behaviors checked here: when set,
the env-var prefix is emitted; when empty, nothing is emitted (no stray
argument, which cmake would warn about).
"""
import pytest

import parts.pieces.cmake  # noqa: F401
import parts.settings as parts_settings


# the exact subst fragment used in the cmake configure command line
PREFIX_FRAGMENT = '${define_if("$CMAKE_PREFIX_PATH","CMAKE_PREFIX_PATH=")}${MAKEPATH("$CMAKE_PREFIX_PATH")}'


@pytest.fixture
def env():
    return parts_settings.DefaultSettings().Environment()


class TestCMakePrefixPathConsumption:
    def test_empty_emits_nothing(self, env):
        # no dependencies -> CMAKE_PREFIX_PATH unset -> no stray token on the
        # cmake command line (a bare '' would make cmake warn)
        assert env.subst(PREFIX_FRAGMENT) == ''

    def test_single_path_emits_env_assignment(self, env):
        env['CMAKE_PREFIX_PATH'] = ['/sdk/lib/cmake']
        assert env.subst(PREFIX_FRAGMENT) == 'CMAKE_PREFIX_PATH=/sdk/lib/cmake'

    def test_multiple_paths_are_separated(self, env):
        env['CMAKE_PREFIX_PATH'] = ['/a/lib/cmake', '/b/lib/cmake']
        out = env.subst(PREFIX_FRAGMENT)
        assert out.startswith('CMAKE_PREFIX_PATH=')
        # path list joined with the platform separator
        import os
        assert out == 'CMAKE_PREFIX_PATH=' + os.pathsep.join(['/a/lib/cmake', '/b/lib/cmake'])
