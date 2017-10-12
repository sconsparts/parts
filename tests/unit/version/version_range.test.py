import unittest
from parts.version import *


class TestVersionRange(unittest.TestCase):

    def test_version_range_single(self):
        '''Test that a range with one version works correctly.'''
        ver = version(1.0)
        range = version_range('1.0')
        self.assertTrue(ver in range)
        self.assertFalse('1.1' in range)
        self.assertTrue('1.0' in range)
        self.assertTrue(1.0 in range)

    def test_version_range_upper(self):
        '''Test that a range with one upper version works.'''
        ver = version(1.0)
        range = version_range('-2.0')
        self.assertTrue(ver in range)
        self.assertTrue('0.9' in range)
        self.assertFalse('2.0' in range)

    def test_version_range_single_wildcard(self):
        '''Test that a range with a single wildcard version works.'''
        ver = version(1.9)
        range = version_range('1.*')
        self.assertTrue(ver in range)
        self.assertFalse(0.9 in range)
        self.assertFalse(2.0 in range)

    def test_version_range_wildcard(self):
        '''Test that a range with wildcards works.'''
        ver = version(2.0)
        range = version_range('0.9-1.*')
        self.assertFalse(ver in range)
        self.assertTrue(0.9 in range)
        self.assertTrue('1.9.1' in range)
        self.assertFalse('2.0beta' in range)

    def test_version_range_bignum(self):
        '''Test that big numbers can be accepted.'''
        range = version_range('1-*')
        self.assertTrue(99999999999999999 in range)

    def test_version_range_not_single(self):
        '''Test that a single not version number works.'''
        range = version_range('!1.5')
        self.assertFalse('1.5' in range)

    def test_version_range_not_range(self):
        '''Test that a single not version range works.'''
        range = version_range('!1.5-1.9')
        self.assertFalse('1.6' in range)

        # Should 1.9 be in '!1.5-1.9'?
        self.assertTrue('1.9' in range)

        self.assertTrue('2.0' in range)

    def test_version_range_include_exclude(self):
        '''Test that include and exclude relation works.'''
        range = version_range('1.0-2.0, !1.4.5-1.4.7')
        self.assertTrue(1.0 in range)
        self.assertFalse('1.4.5' in range)
        self.assertFalse('3.0' in range)

        # Should 1.4.7 be in '1.0-2.0, !1.4.5-1.4.7'?
        self.assertTrue('1.4.7' in range)

    def test_version_range_empty(self):
        '''Test that an empty version range always accepts.'''
        range = version_range()
        self.assertTrue(1.0 in range)
        self.assertFalse('10.1beta' not in range)

        range = version_range('')
        self.assertTrue(1.0 in range)
        self.assertFalse('10.1beta' not in range)

    def test_version_range_half_empty(self):
        '''Test that a half-empty version range still works.'''
        range = version_range(',!2.0')
        self.assertTrue(1.0 in range)
        self.assertFalse(2.0 in range)

    def test_version_range_split(self):
        '''Test that a non-contitous range works.'''
        range = version_range('1.0-2.0, 3.0-4.0')
        self.assertTrue(1.0 in range)
        self.assertTrue(2.0 not in range)
        self.assertTrue('3.0.1' in range)
        self.assertTrue(4.0 not in range)

    def test_version_range_inclusive(self):
        '''Test inclusive top and bottom range.'''
        range = version_range('[1-2]')
        self.assertTrue(2.0 in range)
        self.assertFalse('2.0.1' in range)
        self.assertTrue(1.0 in range)

    def test_version_range_exclusive(self):
        '''Test exclusive bottom and inclusive top.'''
        range = version_range('(1-2]')
        self.assertTrue(2.0 in range)
        self.assertFalse('2.0.1' in range)
        self.assertFalse(1.0 in range)
        self.assertTrue('1.0.1' in range)
        self.assertTrue('1.0beta' not in range)

    def test_version_range_whitespace(self):
        '''Test that whitespace has no affect on range.'''
        range = version_range("[1\t-\t\t2\n.*   \r]")
        range = version_range('(1-2]')
        self.assertTrue(2.0 in range)
        self.assertFalse('2.0.1' in range)
        self.assertFalse(1.0 in range)
        self.assertTrue('1.0.1' in range)
        self.assertTrue('1.0beta' not in range)

    def test_version_range_not_position(self):
        '''Test that not can be inside or outside bracket.'''
        range = version_range('1-2, ![1.5-1.6]')
        self.assertTrue(1.4 in range)
        self.assertTrue('1.5.4' not in range)
        self.assertTrue('1.6.1' in range)
        self.assertTrue(0.1 not in range)

        range = version_range('1-2, [!1.5-1.6]')
        self.assertTrue(1.4 in range)
        self.assertTrue('1.5.4' not in range)
        self.assertTrue('1.6.1' in range)
        self.assertTrue(0.1 not in range)

    def test_version_range_bestof(self):
        '''Test that the best version is retrieved from a list.'''
        range = version_range('1-2, !1.5-1.6.1, 2.5-3')
        verlist = [
            version('1.0'),
            '1.6',
        ]

        self.assertEqual(range.bestVersion(verlist), '1.0')

        verlist.append(1.7)
        self.assertEqual(range.bestVersion(verlist), '1.7')

        verlist.append(2.4)
        self.assertEqual(range.bestVersion(verlist), '1.7')

        verlist.append('2.6beta1')
        self.assertEqual(range.bestVersion(verlist), '2.6beta1')

    def test_version_range_0(self):
        '''Test that that version of 0 is found in range of *'''
        range = version_range('*')
        ver = version('0.0.0')
        self.assertTrue(ver in range)
        ver = version('0.0')
        self.assertTrue(ver in range)
        ver = version('0')
        self.assertTrue(ver in range)
