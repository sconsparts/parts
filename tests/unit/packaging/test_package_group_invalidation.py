'''Tests that PackageGroup() invalidates the sorted package data.

SortPackageGroups() keeps a sorted view of which installed nodes belong to which
package group, and skips the work when nothing has changed:

    if g_known_num_of_install_files == current_num and not g_resort_package_data:
        return

so the only thing that forces a re-sort when group membership changes without the
installed-file count changing is g_resort_package_data. PackageGroup() set that
name without declaring it global, which bound a local and threw it away, and the
re-sort never happened.

That matters most for ReplacePackageGroupCriteria / Append / Prepend: their whole
job is to change how nodes are filtered into groups, and the PackageGroup(name)
call at the end is their only cache invalidation.
'''
import threading
import unittest

import parts.packaging as packaging
import parts.settings as settings


class TestPackageGroupInvalidation(unittest.TestCase):

    def setUp(self):
        # PackageGroup() substs the name through the default environment
        self.env = settings.DefaultSettings().Environment()
        self._saved_flag = packaging.g_resort_package_data
        self._saved_groups = dict(packaging.g_package_groups)
        # start from "everything is sorted and up to date"
        packaging.g_resort_package_data = False

    def tearDown(self):
        packaging.g_resort_package_data = self._saved_flag
        packaging.g_package_groups.clear()
        packaging.g_package_groups.update(self._saved_groups)

    def test_adding_a_part_marks_the_sorted_data_stale(self):
        packaging.PackageGroup('test_group_with_parts', ['some_part_alias'])
        self.assertTrue(packaging.g_resort_package_data)

    def test_naming_a_group_alone_marks_the_sorted_data_stale(self):
        # this is the form the criteria functions use: no parts, called purely to
        # invalidate after changing a filter
        packaging.PackageGroup('test_group_no_parts')
        self.assertTrue(packaging.g_resort_package_data)

    def test_the_part_is_actually_recorded(self):
        packaging.PackageGroup('test_group_records', ['part_a'])
        packaging.PackageGroup('test_group_records', ['part_b'])
        self.assertEqual(packaging.g_package_groups['test_group_records'],
                         {'part_a', 'part_b'})

    def test_an_empty_name_does_not_invalidate(self):
        # PackageGroup returns early for an empty name without touching anything
        self.assertEqual(packaging.PackageGroup(''), tuple())
        self.assertFalse(packaging.g_resort_package_data)

    def test_invalidation_during_a_sort_survives_it(self):
        # SortPackageGroups() clears the flag before its pass rather than after,
        # so a PackageGroup() call made while it runs still forces another sort.
        # A PACKAGE_NODE_FILTER callback can reach PackageGroup() on the sorting
        # thread, and g_sort_data_lock is an RLock, so holding the lock is not
        # enough on its own.
        packaging.g_resort_package_data = True
        with packaging.g_sort_data_lock:
            packaging.SortPackageGroups()
            # stands in for a filter callback firing mid-pass
            packaging.PackageGroup('test_group_midsort', ['part_m'])
        self.assertTrue(packaging.g_resort_package_data)

    def test_invalidation_is_visible_to_another_thread(self):
        # the flag has to reach the module, not a frame that is about to be
        # discarded, or a concurrent sort will not see it
        def add():
            packaging.PackageGroup('test_group_threaded', ['part_x'])

        worker = threading.Thread(target=add)
        worker.start()
        worker.join(timeout=30)
        self.assertFalse(worker.is_alive())
        self.assertTrue(packaging.g_resort_package_data)


if __name__ == '__main__':
    unittest.main()
