"""Tests for non-default git-ssh username support.

A ScmGit using the ``git`` (ssh) protocol builds a
``<user>@<server>:<repo>.git`` clone URL. The username is the ``username=``
argument if given, otherwise the ``$GIT_DEFAULT_SSH_USER`` variable (default
``git``, which preserves the historical hardcoded ``git@`` URL). An empty user
leaves ``user@`` out. A user other than ``git`` also keeps its own mirror and
extern checkout. The https / file / local protocols are unaffected.
"""
import hashlib
from pathlib import Path

import pytest

import parts.scm.git as git_scm
import parts.settings as parts_settings


@pytest.fixture
def env():
    return parts_settings.DefaultSettings().Environment()


def make_git(env, protocol='git', username=None):
    # an explicit protocol avoids depending on $GIT_PROTOCOL; the scm base
    # constructor only assigns attributes, so no live build is needed.
    obj = git_scm.git('myrepo', server='git.example.com', protocol=protocol, username=username)
    obj._env = env
    return obj


class TestGitDefaultSshUser:
    def test_registered_default_is_git(self, env):
        assert env['GIT_DEFAULT_SSH_USER'] == 'git'


class TestUsernameProperty:
    def test_defaults_to_git_default_ssh_user(self, env):
        assert make_git(env).Username == 'git'

    def test_explicit_username_wins(self, env):
        assert make_git(env, username='alice').Username == 'alice'

    def test_follows_env_override(self, env):
        env['GIT_DEFAULT_SSH_USER'] = 'svc'
        assert make_git(env).Username == 'svc'


class TestFullPathSshUrl:
    def test_default_user_preserves_legacy_url(self, env):
        # backward compatible: with the default user the ssh URL is unchanged
        assert make_git(env).FullPath == 'git@git.example.com:myrepo.git'

    def test_explicit_username_in_url(self, env):
        assert make_git(env, username='alice').FullPath == 'alice@git.example.com:myrepo.git'

    def test_env_default_user_in_url(self, env):
        env['GIT_DEFAULT_SSH_USER'] = 'svc'
        assert make_git(env).FullPath == 'svc@git.example.com:myrepo.git'

    def test_https_url_ignores_username(self, env):
        # username only affects the git-ssh (git@) protocol
        assert make_git(env, protocol='https', username='alice').FullPath == 'https://git.example.com/myrepo.git'


class TestEmptyUsername:
    def test_empty_username_leaves_the_user_out(self, env):
        # no user in the URL, so ssh takes the User from its configuration
        assert make_git(env, username='').FullPath == 'git.example.com:myrepo.git'

    def test_empty_default_user_leaves_the_user_out(self, env):
        env['GIT_DEFAULT_SSH_USER'] = ''
        assert make_git(env).FullPath == 'git.example.com:myrepo.git'


def _legacy_request_hash(server, repository, branch):
    # what the extern request hash was before the user could be chosen
    md5 = hashlib.md5()
    md5.update(server.encode())
    md5.update(repository.encode())
    md5.update(branch.encode())
    return md5.hexdigest()


class TestCacheIdentity:
    """Two ssh users can reach two different repositories through the same URL
    path, so they must not share a mirror or an extern checkout. The default
    user keeps the paths it always had."""

    def test_default_user_keeps_the_mirror_path(self, env):
        cache = env.subst('$SCM_GIT_CACHE_DIR')
        assert make_git(env).MirrorPath == Path(cache) / 'git.example.com' / 'myrepo.git'

    def test_default_user_keeps_the_request_hash(self, env):
        assert make_git(env)._request_hash() == _legacy_request_hash('git.example.com', 'myrepo', '')

    def test_users_get_their_own_mirror(self, env):
        alice = make_git(env, username='alice').MirrorPath
        bob = make_git(env, username='bob').MirrorPath
        assert alice != bob
        assert alice != make_git(env).MirrorPath

    def test_users_get_their_own_extern_checkout(self, env):
        alice = make_git(env, username='alice')._request_hash()
        bob = make_git(env, username='bob')._request_hash()
        assert alice != bob
        assert alice != make_git(env)._request_hash()

    def test_none_default_user_is_the_empty_user(self, env):
        env['GIT_DEFAULT_SSH_USER'] = None
        obj = make_git(env)
        assert obj.FullPath == 'git.example.com:myrepo.git'
        assert obj.MirrorPath == make_git(env, username='').MirrorPath

    def test_empty_user_is_its_own_identity(self, env):
        assert make_git(env, username='').MirrorPath != make_git(env).MirrorPath
        assert make_git(env, username='')._request_hash() != make_git(env)._request_hash()

    def test_https_ignores_the_user(self, env):
        https_alice = make_git(env, protocol='https', username='alice')
        https_default = make_git(env, protocol='https')
        assert https_alice.MirrorPath == https_default.MirrorPath
        assert https_alice._request_hash() == https_default._request_hash()
