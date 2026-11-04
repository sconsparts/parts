"""Tests for the GEN_PKG_RUNPATHS mapper and the RUNPATH it generates for packages.

A packaged binary gets a RUNPATH built from the $ORIGIN-relative and absolute
forms of the package lib location. With the default PACKAGE_ROOT of "/" the
absolute form degenerates to /lib, which the dynamic loader already searches and
which rpmbuild's check-rpaths rejects outright ("contains a standard runpath").
This pins that absolute entries resolving to a default loader path are dropped,
that a real install prefix keeps its absolute path, and that the $ORIGIN-relative
entries are never touched.
"""
import sys

import pytest

import parts.settings as parts_settings
import parts.pieces.rpm_package  # noqa: F401 - registers the _RPM_*_RUNPATH variables
from parts.mappers import pkgrunpath_mapper

# RUNPATH is a posix concept, and the generated values are quoted per host OS
pytestmark = pytest.mark.skipif(sys.platform == 'win32', reason="RUNPATH generation is posix only")


@pytest.fixture
def env():
    return parts_settings.DefaultSettings().Environment()


class TestRegisteredDefaults:
    def test_loader_default_paths(self, env):
        assert env['PACKAGE_LOADER_DEFAULT_PATHS'] == ['/lib', '/lib64', '/usr/lib', '/usr/lib64']


class TestGeneratedPackageRunpath:
    '''
    End to end through the registered variables, which is what the rpm builder
    actually substitutes. The $$ is SCons escaping: it reaches patchelf as $ORIGIN.
    '''

    def test_default_package_root_drops_lib(self, env):
        # PACKAGE_ROOT="/" makes PACKAGE_LIB resolve to /lib
        assert env.subst('$_RPM_SELF_ABS_RUNPATH') == ''
        assert env.subst('$_RPM_RUNPATH') == "'$$ORIGIN/../lib'"

    def test_real_prefix_keeps_absolute_path(self, env):
        env['PACKAGE_ROOT'] = '/opt/mypkg'
        assert env.subst('$_RPM_SELF_ABS_RUNPATH') == '/opt/mypkg/lib'
        assert env.subst('$_RPM_RUNPATH') == "'$$ORIGIN/../lib':/opt/mypkg/lib"

    def test_usr_prefix_is_also_a_loader_default(self, env):
        env['PACKAGE_ROOT'] = '/usr'
        assert env.subst('$_RPM_SELF_ABS_RUNPATH') == ''

    def test_filter_can_be_disabled(self, env):
        # clearing the variable restores the previous behavior exactly -- this is
        # the value check-rpaths rejects, so it doubles as the regression guard
        env['PACKAGE_LOADER_DEFAULT_PATHS'] = []
        assert env.subst('$_RPM_RUNPATH') == "'$$ORIGIN/../lib':/lib"


class TestPkgRunPathMapper:
    '''Mapper level cases the registered variables do not reach on their own.'''

    def call(self, env, mapper):
        return mapper._guarded_call(None, None, env, False)

    def test_only_default_loader_paths_are_filtered(self, env):
        ret = self.call(env, pkgrunpath_mapper(
            ['/usr/lib64', '/opt/mypkg/lib', '/lib'], bin_path='/bin', use_origin=False))
        assert ret == ['/opt/mypkg/lib']

    def test_origin_relative_is_never_filtered(self, env):
        ret = self.call(env, pkgrunpath_mapper('/lib', bin_path='/bin'))
        assert len(ret) == 1
        assert '../lib' in str(ret[0])

    def test_skip_paths_is_part_of_the_signature(self):
        # __repr__ feeds _get_cache_hash, so a different filter must not collide
        # with a previously cached subst result
        a = pkgrunpath_mapper('/lib', bin_path='/bin', use_origin=False)
        b = pkgrunpath_mapper('/lib', bin_path='/bin', use_origin=False, skip_paths=[])
        assert repr(a) != repr(b)
