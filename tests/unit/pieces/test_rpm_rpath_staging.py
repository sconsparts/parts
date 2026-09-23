"""Tests for rpm_package.rpath_staging_prefix.

The rpm scanner rewrites the runpath of binaries/libraries into a temporary
staging location before packaging. Two rpath-rewritable files that share a
basename but install to different paths must stage to distinct locations, or
SCons fails with two builders writing the same target. This pins the three
disambiguation modes: an explicit sub_dir MetaTag, the
RPM_PACKAGE_FILE_DIFFERS_PATH opt-in, and the default (no extra subdir) for a
node that carries no sub_dir MetaTag.
"""
import itertools
import types

import pytest

import parts.pieces.rpm_package as rpm_package
import parts.settings as parts_settings


BASE = "$BUILD_DIR/_RPM_RUNPATH_${PART_MINI_SIG}/LIB"


def _node(dirpath):
    # minimal stand-in for an SCons node: only .dir.rstr() is used
    return types.SimpleNamespace(dir=types.SimpleNamespace(rstr=lambda: dirpath))


_node_ids = itertools.count()


def _installed(env, sub_dir=None):
    # the installed node the scanner reads the sub_dir MetaTag from. InstallItem
    # tags it in the 'package' namespace, and only when a sub_dir was given; a
    # fresh node per call, so no tag leaks from one test into the next
    node = env.File(f'staged{next(_node_ids)}.so')
    if sub_dir is not None:
        env.MetaTag(node, 'package', sub_dir=sub_dir)
    return node


@pytest.fixture
def env():
    return parts_settings.DefaultSettings().Environment()


class TestRpathStagingPrefix:
    def test_default_appends_nothing(self, env):
        # a node with no sub_dir MetaTag appends nothing, which is also what
        # leaves room for the RPM_PACKAGE_FILE_DIFFERS_PATH branch
        assert rpm_package.rpath_staging_prefix(env, 'LIB', _installed(env), None) == BASE

    def test_explicit_sub_dir_is_appended(self, env):
        # read from the 'package' namespace InstallItem writes; looking in any
        # other namespace finds nothing and the explicit sub_dir is ignored
        assert rpm_package.rpath_staging_prefix(env, 'LIB', _installed(env, 'plugins'), None) == BASE + "/plugins"

    def test_differs_path_appends_install_relative_subpath(self, env):
        env['RPM_PACKAGE_FILE_DIFFERS_PATH'] = True
        env['INSTALL_LIB'] = '/opt/install/lib'
        node = _node('/opt/install/lib/extra')
        assert rpm_package.rpath_staging_prefix(env, 'LIB', _installed(env), node) == BASE + "/extra"

    def test_differs_path_off_by_default(self, env):
        # opt-in: without the flag, the install-relative subpath is not used
        env['INSTALL_LIB'] = '/opt/install/lib'
        node = _node('/opt/install/lib/extra')
        assert rpm_package.rpath_staging_prefix(env, 'LIB', _installed(env), node) == BASE

    def test_explicit_sub_dir_wins_over_differs_path(self, env):
        env['RPM_PACKAGE_FILE_DIFFERS_PATH'] = True
        env['INSTALL_LIB'] = '/opt/install/lib'
        node = _node('/opt/install/lib/extra')
        assert rpm_package.rpath_staging_prefix(env, 'LIB', _installed(env, 'plugins'), node) == BASE + "/plugins"

    def test_flag_registered_default_false(self, env):
        assert env['RPM_PACKAGE_FILE_DIFFERS_PATH'] is False
