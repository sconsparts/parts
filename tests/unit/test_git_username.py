"""Tests for non-default git-ssh username support.

A git extern using the ``git`` (ssh) protocol builds a
``<user>@<server>:<repo>.git`` clone URL. The username is the per-extern
``username=`` argument if given, otherwise the ``$GIT_DEFAULT_SSH_USER``
variable (default ``git``, which preserves the historical hardcoded ``git@``
URL). The https / file / local protocols are unaffected.
"""
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
