"""Tests for rpm_package.rpath_staging_prefix.

The rpm scanner rewrites the runpath of binaries/libraries into a temporary
staging location before packaging. Two rpath-rewritable files that share a
basename but install to different paths must stage to distinct locations, or
SCons fails with two builders writing the same target. This pins the three
disambiguation modes: explicit sub_dir, the RPM_PACKAGE_FILE_DIFFERS_PATH
opt-in, and the default (no extra subdir).
"""
import types

import pytest

import parts.pieces.rpm_package as rpm_package
import parts.settings as parts_settings


BASE = "$BUILD_DIR/_RPM_RUNPATH_${PART_MINI_SIG}/LIB"


def _node(dirpath):
    # minimal stand-in for an SCons node: only .dir.rstr() is used
    return types.SimpleNamespace(dir=types.SimpleNamespace(rstr=lambda: dirpath))


@pytest.fixture
def env():
    return parts_settings.DefaultSettings().Environment()


class TestRpathStagingPrefix:
    def test_default_appends_nothing(self, env):
        # Regression guard: an unset sub_dir must NOT append anything.
        # The original code defaulted the sub_dir MetaTag lookup to 'package',
        # which appended '/package' to every node and made the
        # RPM_PACKAGE_FILE_DIFFERS_PATH branch unreachable.
        assert rpm_package.rpath_staging_prefix(env, 'LIB', '', None) == BASE

    def test_explicit_sub_dir_is_appended(self, env):
        assert rpm_package.rpath_staging_prefix(env, 'LIB', 'plugins', None) == BASE + "/plugins"

    def test_differs_path_appends_install_relative_subpath(self, env):
        env['RPM_PACKAGE_FILE_DIFFERS_PATH'] = True
        env['INSTALL_LIB'] = '/opt/install/lib'
        node = _node('/opt/install/lib/extra')
        assert rpm_package.rpath_staging_prefix(env, 'LIB', '', node) == BASE + "/extra"

    def test_differs_path_off_by_default(self, env):
        # opt-in: without the flag, the install-relative subpath is not used
        env['INSTALL_LIB'] = '/opt/install/lib'
        node = _node('/opt/install/lib/extra')
        assert rpm_package.rpath_staging_prefix(env, 'LIB', '', node) == BASE

    def test_explicit_sub_dir_wins_over_differs_path(self, env):
        env['RPM_PACKAGE_FILE_DIFFERS_PATH'] = True
        env['INSTALL_LIB'] = '/opt/install/lib'
        node = _node('/opt/install/lib/extra')
        assert rpm_package.rpath_staging_prefix(env, 'LIB', 'plugins', node) == BASE + "/plugins"

    def test_flag_registered_default_false(self, env):
        assert env['RPM_PACKAGE_FILE_DIFFERS_PATH'] is False
