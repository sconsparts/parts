'''Tests for the invalidation of the sorted package data.

SortPackageGroups() keeps a sorted view of which installed nodes belong to which
package group, and skips the work when nothing has changed:

    if g_known_num_of_install_files == current_num and not g_resort_package_data:
        return

so with the installed-file count unchanged, only g_resort_package_data forces a
re-sort. PackageGroup() set that name without declaring it global, which bound a
local and threw it away, so the re-sort it asked for never happened.

A re-sort does not apply a changed PACKAGE_GROUP_FILTER criterion to a file that
is already sorted: the first sort records the file's groups on the file, and later
sorts use those. It does run the PACKAGE_NODE_FILTER callbacks again, so a
callback that now returns another group puts the file in it.

The tests also cover a failed pass being run again, and a caller on another
thread waiting for a pass in progress. They run real SortPackageGroups() passes
over one stand-in installed node, with the engine's def_env and _part_manager and
the installed-file list patched.
'''
import contextlib
import threading
import types
import unittest
from unittest import mock

import SCons.Tool.install

import parts.core.util as common
import parts.packaging as packaging


class _InstalledNode:
    '''Just enough of an installed File node for SortPackageGroups().'''

    def __init__(self, name):
        self.ID = name
        self.attributes = types.SimpleNamespace(package=common.namespace(part_alias='test_part'))


class TestPackageGroupInvalidation(unittest.TestCase):

    def setUp(self):
        self._saved_flag = packaging.g_resort_package_data
        self._saved_known = packaging.g_known_num_of_install_files
        self._saved_groups = dict(packaging.g_package_groups)
        self._saved_sorted = tuple(dict(groups) for groups in packaging._sorted_groups)
        self.node = _InstalledNode('test_installed_file')
        self.thread_errors = []
        # start from "everything is sorted and up to date"
        packaging.g_resort_package_data = False
        packaging.g_known_num_of_install_files = 1

    def tearDown(self):
        packaging.g_resort_package_data = self._saved_flag
        packaging.g_known_num_of_install_files = self._saved_known
        packaging.g_package_groups.clear()
        packaging.g_package_groups.update(self._saved_groups)
        for groups, saved in zip(packaging._sorted_groups, self._saved_sorted):
            groups.clear()
            groups.update(saved)

    @contextlib.contextmanager
    def _installed(self, node_filter):
        '''self.node is the one installed file, and node_filter the one
        PACKAGE_NODE_FILTER callback, for SortPackageGroups() calls made inside.'''
        # both are properties of the engine class, so they are patched there
        engine_class = type(packaging.glb.engine)
        part = types.SimpleNamespace(PackageGroup='test_group_default')
        part_manager = types.SimpleNamespace(_from_alias=lambda alias: part)
        def_env = {'PACKAGE_GROUP_FILTER': {}, 'PACKAGE_NODE_FILTER': [node_filter]}
        with mock.patch.object(engine_class, 'def_env', new_callable=mock.PropertyMock, return_value=def_env), \
                mock.patch.object(engine_class, '_part_manager', new_callable=mock.PropertyMock, return_value=part_manager), \
                mock.patch.object(SCons.Tool.install, '_INSTALLED_FILES', [self.node]):
            yield

    def _next_call_sorts(self):
        seen = []
        with self._installed(lambda node: seen.append(node.ID)):
            packaging.SortPackageGroups()
        return seen == [self.node.ID]

    def _thread(self, target):
        '''A thread running target; what it raises goes to self.thread_errors.'''
        def run():
            try:
                target()
            except BaseException as e:
                self.thread_errors.append(e)
        return threading.Thread(target=run)

    def test_up_to_date_data_is_not_sorted_again(self):
        self.assertFalse(self._next_call_sorts())
        # forced by the flag
        packaging.g_resort_package_data = True
        self.assertTrue(self._next_call_sorts())
        self.assertFalse(self._next_call_sorts())
        # forced by a new installed file
        packaging.g_known_num_of_install_files = 0
        self.assertTrue(self._next_call_sorts())
        self.assertFalse(self._next_call_sorts())

    def test_adding_a_part_marks_the_sorted_data_stale(self):
        packaging.PackageGroup('test_group_with_parts', ['some_part_alias'])
        self.assertTrue(self._next_call_sorts())

    def test_naming_a_group_alone_marks_the_sorted_data_stale(self):
        # this is the form the criteria functions use: no parts, called mainly
        # to invalidate after changing a filter
        packaging.PackageGroup('test_group_no_parts')
        self.assertTrue(self._next_call_sorts())

    def test_the_part_is_actually_recorded(self):
        packaging.PackageGroup('test_group_records', ['part_a'])
        packaging.PackageGroup('test_group_records', ['part_b'])
        self.assertEqual(packaging.g_package_groups['test_group_records'],
                         {'part_a', 'part_b'})

    def test_an_empty_name_does_not_invalidate(self):
        # PackageGroup returns early for an empty name without touching anything
        self.assertEqual(packaging.PackageGroup(''), tuple())
        self.assertFalse(self._next_call_sorts())

    def test_a_node_filter_group_added_later_is_picked_up(self):
        # what a re-sort forced by PackageGroup() does change for a file that is
        # already sorted: the PACKAGE_NODE_FILTER callbacks run again, so a
        # filter that now returns another group puts the file in it
        late_groups = []
        packaging.g_known_num_of_install_files = 0
        with self._installed(lambda node: late_groups):
            self.assertEqual(packaging.GetPackageGroupFiles('test_group_default'), [self.node])
            late_groups.append('test_group_late')
            packaging.PackageGroup('test_group_late')
            files = packaging.GetPackageGroupFiles('test_group_late')
        self.assertEqual(files, [self.node])

    def test_invalidation_during_a_sort_survives_it(self):
        # SortPackageGroups() clears the flag before its pass rather than after,
        # so a PackageGroup() call made during the pass, here by a
        # PACKAGE_NODE_FILTER callback on the sorting thread, still forces
        # another sort, and only one
        def node_filter(node):
            packaging.PackageGroup('test_group_midsort', ['part_m'])

        packaging.g_resort_package_data = True
        with self._installed(node_filter):
            packaging.SortPackageGroups()
        self.assertIn('test_group_midsort', packaging.g_package_groups)
        self.assertTrue(self._next_call_sorts())
        self.assertFalse(self._next_call_sorts())

    def test_a_failed_sort_runs_again(self):
        # a callback that raises leaves the cache partly filled, so the next call
        # has to sort again, whether the flag or a new installed file forced the
        # failed sort
        def raising(exc):
            def node_filter(node):
                raise exc
            return node_filter

        cases = (
            ('flag', True, 1, RuntimeError('filter failed')),
            ('installed file', False, 0, RuntimeError('filter failed')),
            # SCons turns a SystemExit from a scanner or action into a build
            # error and, with -k, keeps building
            ('SystemExit', False, 0, SystemExit(3)),
        )
        for forced_by, flag, known, exc in cases:
            with self.subTest(forced_by=forced_by):
                packaging.g_resort_package_data = flag
                packaging.g_known_num_of_install_files = known
                with self._installed(raising(exc)), self.assertRaises(type(exc)):
                    packaging.SortPackageGroups()
                self.assertTrue(self._next_call_sorts())

    def test_a_caller_waits_for_a_sort_in_progress(self):
        # the flag is cleared when a pass starts, so a caller on another thread
        # must not take the quick return while the pass is still filling the
        # cache: it has to wait for the pass to finish
        in_pass = threading.Event()
        release = threading.Event()

        def node_filter(node):
            in_pass.set()
            release.wait(30)

        packaging.g_resort_package_data = True
        with self._installed(node_filter):
            sorter = self._thread(packaging.SortPackageGroups)
            caller = self._thread(packaging.SortPackageGroups)
            try:
                sorter.start()
                self.assertTrue(in_pass.wait(30))
                caller.start()
                caller.join(timeout=0.5)
                waited = caller.is_alive()
            finally:
                release.set()
                sorter.join(timeout=30)
                if caller.ident is not None:
                    caller.join(timeout=30)
        self.assertEqual(self.thread_errors, [])
        self.assertTrue(waited)
        self.assertFalse(sorter.is_alive() or caller.is_alive())


if __name__ == '__main__':
    unittest.main()
