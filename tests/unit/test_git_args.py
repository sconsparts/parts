"""Tests for the configurable per-subcommand git argument variables.

The git scm command strings reference ${GIT_CLONE_ARGS}, ${GIT_MIRROR_ARGS},
${GIT_FETCH_ARGS}, ${GIT_CHECKOUT_ARGS}, ${GIT_PULL_ARGS}, ${GIT_RESET_ARGS}
and ${GIT_AM_ARGS}. These tests pin their registered defaults and confirm that
clone/mirror progress output is configurable (the historical default is
--progress, but it can be suppressed).
"""
import pytest

import parts.scm.git  # noqa: F401  importing registers the GIT_*_ARGS variables
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

    def test_clone_progress_is_suppressible(self, env):
        # the whole point of registering these: a part can now turn progress off
        env['GIT_CLONE_ARGS'] = ''
        assert env.subst('git clone ${GIT_CLONE_ARGS} repo'.replace('  ', ' ')).split() == [
            'git', 'clone', 'repo'
        ]

    def test_am_args_threaded_into_command(self, env):
        env['GIT_AM_ARGS'] = '--3way'
        assert env.subst('git am ${GIT_AM_ARGS} patch').split() == ['git', 'am', '--3way', 'patch']
