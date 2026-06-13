"""Tests for git scm patch-file handling.

A git extern may declare a single patch file or a list of patch files, which
are applied in list order via ``git am``. These tests guard two invariants:

  * a missing/None patchfile normalizes to an empty list (``_patchfile`` is
    never left unset), so a checkout with no patch never raises AttributeError
    when ``self._patchfile`` is later inspected;
  * ``apply_patch_file`` appends exactly one action per patch (``ret +=
    [Action]``); a bare ``ret += Action`` would instead extend the list by
    iterating a single Action object.
"""
import pytest

import parts.scm.git as git_scm


def make_git(patchfile=None):
    # base.__init__ only assigns attributes, so a git object constructs without
    # parts global state or a live Environment.
    return git_scm.git('example.com/group/repo', patchfile=patchfile)


class _FakeFile:
    def __init__(self, path):
        self.abspath = '/abs/' + path


class _FakeEnv:
    """Minimal env: apply_patch_file only needs File().abspath and Action()."""

    def File(self, path):
        return _FakeFile(path)

    def Action(self, cmd, strval):
        # the displayed command string carries everything we assert on
        return strval


class TestPatchfileNormalization:
    def test_default_is_empty_list(self):
        assert make_git()._patchfile == []

    def test_none_is_empty_list(self):
        # the regression: a missing patchfile must not leave _patchfile unset
        assert make_git(patchfile=None)._patchfile == []

    def test_single_string_becomes_one_element_list(self):
        assert make_git(patchfile='fix.patch')._patchfile == ['fix.patch']

    def test_list_is_preserved_in_order(self):
        assert make_git(patchfile=['a.patch', 'b.patch'])._patchfile == ['a.patch', 'b.patch']

    def test_any_sequence_is_accepted(self):
        assert make_git(patchfile=('a.patch', 'b.patch'))._patchfile == ['a.patch', 'b.patch']


class TestApplyPatchFile:
    def _apply(self, patchfile):
        obj = make_git(patchfile=patchfile)
        obj._env = _FakeEnv()
        return obj.apply_patch_file('cd /work &&')

    def test_no_patch_yields_no_actions(self):
        assert self._apply(None) == []

    def test_single_patch_yields_one_action(self):
        actions = self._apply('fix.patch')
        assert len(actions) == 1
        assert actions[0] == 'cd /work && git am ${GIT_AM_ARGS} "/abs/fix.patch"'

    def test_multiple_patches_yield_one_action_each_in_order(self):
        # regression guard for the missing list-wrapper: each patch must produce
        # exactly one action, in declaration order
        names = ['first.patch', 'second.patch', 'third.patch']
        actions = self._apply(names)
        assert len(actions) == len(names)
        for action, name in zip(actions, names):
            assert action.endswith(f'"/abs/{name}"')

    def test_am_args_placeholder_is_threaded_through(self):
        # patches are applied via `git am ${GIT_AM_ARGS}` so the configurable
        # am args still apply
        assert '${GIT_AM_ARGS}' in self._apply('fix.patch')[0]
