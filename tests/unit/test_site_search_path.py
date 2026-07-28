"""Tests for parts-site search-path resolution (load_module.get_site_directories).

Covers the addition of /usr/local/share/parts (Linux + macOS) and
~/Library/Application Support/parts (macOS), the ordering of the system
search paths, and that the Windows path tolerates a missing ALLUSERSPROFILE
(i.e. syspath stays defined).
"""
import os

import pytest
import SCons.Script

import parts.glb as glb
import parts.load_module as load_module


@pytest.fixture
def resolver(monkeypatch):
    # deterministic install/source roots
    monkeypatch.setattr(glb, 'parts_path', os.path.join(os.sep, 'opt', 'parts'), raising=False)
    monkeypatch.setattr(glb, 'sconstruct_path', os.path.join(os.sep, 'proj'), raising=False)
    # no --use-part-site / --global-part-site overrides -> default (else) branch
    monkeypatch.setattr(SCons.Script, 'GetOption', lambda name: None)
    load_module.g_site_dir_cache.clear()
    yield
    load_module.g_site_dir_cache.clear()


def _dirs(monkeypatch, host, subdir):
    monkeypatch.setattr(glb, '_host_platform', host, raising=False)
    return load_module.get_site_directories(subdir)


def _p(*parts_):
    return os.path.join(*parts_)


class TestUsrLocalShareSearchPath:
    def test_linux_includes_usr_local_share(self, resolver, monkeypatch):
        dirs = _dirs(monkeypatch, 'linux', 'tools')
        assert _p('/usr/local/share/parts', 'parts-site', 'tools') in dirs
        assert _p('/usr/share/parts', 'parts-site', 'tools') in dirs

    def test_linux_usr_share_ordered_before_usr_local_share(self, resolver, monkeypatch):
        dirs = _dirs(monkeypatch, 'linux', 'ordering')
        i_share = dirs.index(_p('/usr/share/parts', 'parts-site', 'ordering'))
        i_local = dirs.index(_p('/usr/local/share/parts', 'parts-site', 'ordering'))
        assert i_share < i_local

    def test_darwin_includes_usr_local_share_and_user_app_support(self, resolver, monkeypatch):
        dirs = _dirs(monkeypatch, 'darwin', 'mactools')
        assert _p('/Library/Application Support/parts', 'parts-site', 'mactools') in dirs
        assert _p('/usr/local/share/parts', 'parts-site', 'mactools') in dirs
        user = _p(os.path.expanduser('~/Library/Application Support/parts'), 'parts-site', 'mactools')
        assert user in dirs


class TestWindowsSearchPathSafety:
    def test_win32_without_allusersprofile_does_not_raise(self, resolver, monkeypatch):
        # The system path list must stay defined even when ALLUSERSPROFILE is
        # absent (e.g. running as a service), otherwise the later
        # localpath + syspath concatenation raises NameError.
        monkeypatch.delenv('ALLUSERSPROFILE', raising=False)
        monkeypatch.delenv('APPDATA', raising=False)
        dirs = _dirs(monkeypatch, 'win32', 'wintools')
        assert isinstance(dirs, list)
        assert dirs  # non-empty (sconstruct/parts paths always present)
