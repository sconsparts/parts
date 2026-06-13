"""Tests for the system-include (-isystem) dependency feature.

A consumer can mark a dependency's headers as "system" so they compile with
$SYSINCPREFIX (-isystem on gcc/clang) instead of -I, suppressing warnings from
that dependency's headers. The routing is expressed through the requirement
layer rather than special-cased in the section processor:

  * a SYSCPPPATH requirement that *reads* a dependency's CPPPATH export but
    *writes* the consumer's SYSCPPPATH (requirement.read_key);
  * SYSTEM_HEADER_DEFAULT, which mirrors DEFAULT but routes headers that way and
    contains no plain CPPPATH (so a system dependency's headers are emitted once
    as -isystem, never both -I and -isystem).

The actual -isystem emission with a real compiler is covered by the
system_includes gold test.
"""
import copy
import os

import pytest

import parts.api.requirement  # noqa: F401  importing registers the requirement sets
import parts.settings as parts_settings
from parts.requirement import requirement, _added_types


PARTS_TOOLS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'parts', 'tools')
)


def _set_keys(name):
    return sorted({r.key for r in _added_types[name][0]})


class TestReadKey:
    def test_defaults_to_key(self):
        assert requirement('CPPPATH', public=True).read_key == 'CPPPATH'

    def test_explicit_read_key(self):
        r = requirement('SYSCPPPATH', read_key='CPPPATH', public=True)
        assert r.key == 'SYSCPPPATH'
        assert r.read_key == 'CPPPATH'

    def test_value_mapper_uses_read_key(self):
        # the delayed/dynamic mapper must read the dependency's CPPPATH export,
        # not its (absent) SYSCPPPATH export
        mapped = requirement('SYSCPPPATH', read_key='CPPPATH', public=True).value_mapper('apart', 'build', False)
        assert "'CPPPATH'" in mapped
        assert "'SYSCPPPATH'" not in mapped

    def test_copy_preserves_read_key(self):
        # requirement_set composition copy.copy()s each requirement
        assert copy.copy(requirement('SYSCPPPATH', read_key='CPPPATH')).read_key == 'CPPPATH'

    def test_serialize_roundtrip_preserves_read_key(self):
        # REQ.Serialize()/Unserialize() reconstructs via requirement(**data)
        rebuilt = requirement(**requirement('SYSCPPPATH', read_key='CPPPATH', public=True).Serialize())
        assert rebuilt.key == 'SYSCPPPATH'
        assert rebuilt.read_key == 'CPPPATH'


class TestSystemRequirementSets:
    def test_syscpppath_set_reads_cpppath(self):
        reqs = list(_added_types['SYSCPPPATH'][0])
        assert len(reqs) == 1
        assert reqs[0].key == 'SYSCPPPATH'
        assert reqs[0].read_key == 'CPPPATH'

    def test_system_headers_has_no_plain_cpppath(self):
        keys = _set_keys('SYSTEM_HEADERS')
        assert 'SYSCPPPATH' in keys
        assert 'CPPDEFINES' in keys
        assert 'CPPPATH' not in keys

    def test_system_header_default_routes_headers_as_system(self):
        keys = _set_keys('SYSTEM_HEADER_DEFAULT')
        # headers come in as SYSCPPPATH, never plain CPPPATH (no -I/-isystem dup)
        assert 'SYSCPPPATH' in keys
        assert 'CPPPATH' not in keys
        # but everything else DEFAULT pulls is still present
        for k in ('LIBS', 'LIBPATH', 'CPPDEFINES', 'RPATHLINK'):
            assert k in keys

    def test_default_is_unchanged(self):
        keys = _set_keys('DEFAULT')
        assert 'CPPPATH' in keys
        assert 'SYSCPPPATH' not in keys


class TestToolWiring:
    # toolchain=[] -> compiler-less env, so we see the generic c++/cc tool
    # defaults rather than the platform compiler's overrides.
    @pytest.fixture
    def env_cxx(self):
        env = parts_settings.DefaultSettings().Environment(toolchain=[])
        env.Tool('c++', toolpath=[PARTS_TOOLS])
        return env

    @pytest.fixture
    def env_cc(self):
        env = parts_settings.DefaultSettings().Environment(toolchain=[])
        env.Tool('cc', toolpath=[PARTS_TOOLS])
        return env

    def test_cxx_defines_syscpppath_and_wires_flags(self, env_cxx):
        assert env_cxx['SYSCPPPATH'] == []
        assert '$_CPPSYSINCFLAGS' in env_cxx['_CCCOMCOM']
        tmpl = env_cxx['_CPPSYSINCFLAGS']
        assert 'SYSINCPREFIX' in tmpl and 'SYSCPPPATH' in tmpl and 'SYSINCSUFFIX' in tmpl

    def test_cc_defines_syscpppath_and_wires_flags(self, env_cc):
        assert env_cc['SYSCPPPATH'] == []
        assert '$_CPPSYSINCFLAGS' in env_cc['_CCCOMCOM']

    def test_generic_base_keeps_incprefix(self, env_cxx):
        # the generic c++/cc base stays -I (safe for toolchains like msvc that
        # don't grok -isystem); gcc/clang override SYSINCPREFIX to -isystem.
        assert env_cxx['SYSINCPREFIX'] == '$INCPREFIX'


class TestGnuToolchainDefault:
    def test_gnu_or_clang_defaults_to_isystem(self):
        # gcc/g++/clang/aocc override the generic base so a system dependency's
        # headers actually compile with -isystem. The default toolchain on
        # Linux/macOS is gnu/clang-like; skip elsewhere (e.g. msvc keeps -I).
        env = parts_settings.DefaultSettings().Environment()
        cc = str(env.get('CC', ''))
        if not any(tag in cc for tag in ('gcc', 'clang')):
            pytest.skip('default toolchain is not gcc/clang-like')
        assert env['SYSINCPREFIX'] == '-isystem '
