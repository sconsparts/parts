import unittest
from parts.mappers import replace_list_items


class Test_replace_list_items(unittest.TestCase):

    def test_direct(self):
        self.assertEqual(['a', 'd0', 'd1'], replace_list_items(['a', 'D'], 'D', ['d0', 'd1']))

    def test_not_present(self):
        self.assertEqual(['a', 'b'], replace_list_items(['a', 'b'], 'C', ['c']))

    def test_diamond(self):
        '''
        This demonstrates a case when Component A depends on B and C which both depend on D
        '''
        self.assertEqual(['a', 'a1', 'd0', 'd1'], replace_list_items(
            replace_list_items(['a', 'B', 'a1', 'C'], 'C', ['d0', 'd1']), 'B', ['d0', 'd1']))

# vim: set et ts=4 sw=4 ai ft=python :
