"""Tests for the configurable per-subcommand git argument variables.

The git scm command strings reference ${GIT_CLONE_ARGS}, ${GIT_MIRROR_ARGS},
${GIT_FETCH_ARGS}, ${GIT_CHECKOUT_ARGS}, ${GIT_PULL_ARGS}, ${GIT_RESET_ARGS}
and ${GIT_AM_ARGS}. These tests pin their registered defaults (clone and
mirror keep the historical --progress) and check that the commands the git
scm object builds reference them. ${GIT_AM_ARGS} is covered by
test_git_patchfile.py.
"""
import pytest

import parts.scm.git as git_scm  # importing registers the GIT_*_ARGS variables
import parts.settings as parts_settings


GIT_ARG_DEFAULTS = {
    'GIT_CLONE_ARGS': '--progress',
    'GIT_MIRROR_ARGS': '--progress',
    'GIT_FETCH_ARGS': '',
    'GIT_CHECKOUT_ARGS': '',
    'GIT_PULL_ARGS': '',
    'GIT_RESET_ARGS': '',
    'GIT_AM_ARGS': '',
}


@pytest.fixture
def env():
    return parts_settings.DefaultSettings().Environment()


class TestGitArgDefaults:
    @pytest.mark.parametrize('var,default', list(GIT_ARG_DEFAULTS.items()))
    def test_registered_with_expected_default(self, env, var, default):
        assert env[var] == default

    def test_clone_default_emits_progress(self, env):
        # default behavior is unchanged from the historical hardcoded --progress
        assert env.subst('${GIT_CLONE_ARGS}') == '--progress'
        assert env.subst('${GIT_MIRROR_ARGS}') == '--progress'


class _RawEnv(dict):
    """Enough of an environment for the git action builders.

    Action() hands back the command string before any substitution, which a
    real Environment.Action() would already have expanded, so the tests see
    which variables each command references.
    """

    def __init__(self, options=None):
        super().__init__(
            GIT_PROTOCOL='https', GIT_SERVER='example.com', GIT_DEFAULT_SSH_USER='git',
            GIT_DEFAULT_BRANCH='main', USE_SCM_CACHE=False, SCM_IGNORE_MODIFIED=False,
            GIT_IGNORE_UNTRACKED=False, SCM_GIT_CACHE_DIR='/cache')
        self.options = options or {}

    def GetOption(self, name):
        return self.options.get(name, False)

    def Action(self, cmd, strval=None):
        return cmd

    def subst(self, value):
        return value


def _git(options=None, **kw):
    obj = git_scm.git('group/repo', **kw)
    obj._env = _RawEnv(options)
    return obj


def _update_commands(monkeypatch, *, branch_changed=False, on_tag=False, options=None):
    obj = _git(options)
    data = {
        'branch': 'main...origin/main', 'tags': [], 'modified': False, 'untracked': False,
        'server': 'https://example.com/group/repo.git', 'revision': 'abc123',
        'short_revision': 'abc123', 'patched': False,
    }
    monkeypatch.setattr(git_scm.git, 'get_git_data', lambda self: data)
    monkeypatch.setattr(git_scm.git, '_server_changed', lambda self, d: False)
    monkeypatch.setattr(git_scm.git, '_branch_changed', lambda self, d: branch_changed)
    monkeypatch.setattr(git_scm.git, '_on_tag', lambda self, d: on_tag)
    return obj.UpdateAction('/work')


class TestCommandsReferenceTheirArgs:
    def test_mirror_clone(self):
        assert '${GIT_MIRROR_ARGS}' in _git().CreateMirrorAction()[0]

    def test_mirror_update(self):
        assert '${GIT_FETCH_ARGS}' in _git().UpdateMirrorAction()[0]

    def test_clone(self):
        assert '${GIT_CLONE_ARGS}' in _git(branch='main').CheckOutAction('/work')[0]

    def test_clone_then_checkout_of_a_revision(self):
        commands = _git(revision='abc123').CheckOutAction('/work')
        assert any('checkout ${GIT_CHECKOUT_ARGS} abc123' in cmd for cmd in commands)

    def test_update_to_another_branch_fetches_and_checks_out(self, monkeypatch):
        commands = _update_commands(monkeypatch, branch_changed=True)
        assert any('fetch' in cmd and '${GIT_FETCH_ARGS}' in cmd for cmd in commands)
        assert any('checkout ${GIT_CHECKOUT_ARGS}' in cmd for cmd in commands)

    def test_update_of_a_branch_pulls(self, monkeypatch):
        commands = _update_commands(monkeypatch)
        assert any('pull ${GIT_PULL_ARGS}' in cmd for cmd in commands)

    def test_clean_update_resets(self, monkeypatch):
        commands = _update_commands(monkeypatch, options={'scm_clean': True})
        assert any('reset ${GIT_RESET_ARGS} --hard' in cmd for cmd in commands)
