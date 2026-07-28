"""Tests for GnuCommon toolchain-detection helpers.

This path (RedHat toolset discovery, version parsing, and the on-disk
scan_query) previously had no coverage. The tests drive the pure logic
directly: RedHatToolsetPaths and scan_query against temp directory trees,
and get_default_ver against stubbed `<tool> --version` output, so nothing
depends on which compilers happen to be installed on the test host.
"""
import os

import pytest

import parts.tools.GnuCommon.common as common
from parts.tools.GnuCommon.common import GnuInfo, RedHatToolsetPaths


def _gnuinfo(test_file='gcc', opt_dirs=None, **kw):
    return GnuInfo(
        install_scanner=[],
        opt_dirs=opt_dirs or [],
        script=None,
        subst_vars={},
        shell_vars={},
        test_file=test_file,
        **kw
    )


class TestRedHatToolsetPaths:
    def test_returns_empty_when_opt_rh_absent(self, monkeypatch):
        monkeypatch.setattr(common.os.path, 'exists', lambda p: False)
        assert RedHatToolsetPaths() == []

    @staticmethod
    def _redirect_opt_rh(monkeypatch, rh):
        # route only '/opt/rh' to our temp tree; capture the real os functions
        # first so the fallback doesn't recurse into the patched versions
        real_exists, real_listdir = os.path.exists, os.listdir
        monkeypatch.setattr(common.os.path, 'exists', lambda p: True if p == '/opt/rh' else real_exists(p))
        monkeypatch.setattr(common.os, 'listdir', lambda p: real_listdir(str(rh)) if p == '/opt/rh' else real_listdir(p))

    def test_matches_devtoolset_and_gcc_toolset(self, tmp_path, monkeypatch):
        rh = tmp_path / 'rh'
        for name in ('devtoolset-7', 'gcc-toolset-12', 'gcc-toolset-13', 'not-a-toolset', 'llvm-toolset-7'):
            (rh / name).mkdir(parents=True)
        self._redirect_opt_rh(monkeypatch, rh)

        got = sorted(RedHatToolsetPaths())
        expected = sorted(
            os.path.join('/opt/rh', d, 'root/usr/bin')
            for d in ('devtoolset-7', 'gcc-toolset-12', 'gcc-toolset-13')
        )
        assert got == expected
        # the default regex must not match llvm-toolset or arbitrary names
        assert not any('llvm-toolset' in p or 'not-a-toolset' in p for p in got)

    def test_custom_regex_matches_llvm_toolset(self, tmp_path, monkeypatch):
        rh = tmp_path / 'rh'
        for name in ('llvm-toolset-7', 'gcc-toolset-12'):
            (rh / name).mkdir(parents=True)
        self._redirect_opt_rh(monkeypatch, rh)

        got = RedHatToolsetPaths(r"llvm\-toolset\-(?:[0-9]+\.[0-9]+|[0-9]+)")
        assert got == [os.path.join('/opt/rh', 'llvm-toolset-7', 'root/usr/bin')]


class TestGetDefaultVer:
    def test_parses_version_from_tool_output(self, tmp_path, monkeypatch):
        tool = tmp_path / 'gcc'
        tool.write_text('')  # must be an existing file
        monkeypatch.setattr(
            common.subprocess, 'check_output',
            lambda *a, **k: b'gcc (GCC) 13.2.0\nCopyright (C) 2023\n')
        assert _gnuinfo().get_default_ver(str(tool)) == '13.2.0'

    def test_returns_none_for_missing_file(self):
        assert _gnuinfo().get_default_ver('/nonexistent/gcc') is None

    def test_custom_version_pattern(self, tmp_path, monkeypatch):
        tool = tmp_path / 'clang'
        tool.write_text('')
        monkeypatch.setattr(
            common.subprocess, 'check_output',
            lambda *a, **k: b'clang version 17.0.6 (tags/...)\n')
        info = _gnuinfo(test_file='clang', version_pattern=r'clang version ([0-9]+\.[0-9]+\.[0-9]+)')
        assert info.get_default_ver(str(tool)) == '17.0.6'


class TestScanQuery:
    def _info_with_stubbed_version(self, monkeypatch, test_file='gcc', **kw):
        info = _gnuinfo(test_file=test_file, **kw)
        # treat every candidate path as an existing tool whose version is the
        # numeric suffix of its filename (e.g. gcc-13 -> 13.0.0), else 0.0.0
        def fake_ver(path):
            # mirror the real get_default_ver: only existing files have a version
            if not os.path.isfile(path):
                return None
            base = os.path.basename(path)
            m = base.rsplit('-', 1)
            return (m[1] + '.0.0') if len(m) == 2 and m[1].isdigit() else '0.0.0'
        monkeypatch.setattr(info, 'get_default_ver', fake_ver)
        return info

    def test_install_root_finds_versioned_and_plain(self, tmp_path, monkeypatch):
        binroot = tmp_path / 'bin'
        binroot.mkdir()
        for name in ('gcc', 'gcc-12', 'gcc-13', 'ld', 'clang'):
            (binroot / name).write_text('')
        info = self._info_with_stubbed_version(monkeypatch)
        found = info.scan_query(str(binroot), opt_scan=False)

        # gcc (->0.0.0), gcc-12 (->12.0.0), gcc-13 (->13.0.0) discovered; ld/clang ignored
        assert set(found.keys()) == {'0.0.0', '12.0.0', '13.0.0'}
        assert found['13.0.0'] == (str(binroot), str(binroot / 'gcc-13'))
        assert os.path.basename(found['0.0.0'][1]) == 'gcc'

    def test_no_matches_returns_none(self, tmp_path, monkeypatch):
        binroot = tmp_path / 'bin'
        binroot.mkdir()
        for name in ('ld', 'ar', 'clang'):
            (binroot / name).write_text('')
        info = self._info_with_stubbed_version(monkeypatch)
        assert info.scan_query(str(binroot), opt_scan=False) is None

    def test_opt_scan_finds_toolset_bin_layout(self, tmp_path, monkeypatch):
        # opt_dir/<toolset>/bin/<tool> layout, like /opt/rh/gcc-toolset-13/.../bin/gcc
        opt = tmp_path / 'opt'
        toolbin = opt / 'gcc-13' / 'bin'
        toolbin.mkdir(parents=True)
        (toolbin / 'gcc').write_text('')
        info = self._info_with_stubbed_version(monkeypatch, opt_dirs=[str(opt)], opt_pattern=r'gcc\-[0-9]+')
        found = info.scan_query(None, opt_scan=True)
        assert found is not None
        assert any(os.path.basename(p[1]) == 'gcc' and 'bin' in p[0] for p in found.values())
