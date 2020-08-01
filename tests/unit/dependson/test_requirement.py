import unittest
import SCons.Script
from parts.requirement import *


class TestRequirement(unittest.TestCase):

    def setUp(self):
        pass

    def test_requirement_creation(self):
        '''test requirement creation on defined value'''
        tmp = REQ.CPPPATH  # defined "set" value
        for i in tmp:
            self.assertEqual(i.key, 'CPPPATH')
            self.assertEqual(i.is_internal, False)
            self.assertEqual(i.is_public, True)

    def test_requirement_creation1(self):
        '''test requirement creation on defined value internal'''
        tmp = REQ.CPPPATH_internal  # defined "set" value
        for i in tmp:
            self.assertEqual(i.key, 'CPPPATH')
            self.assertEqual(i.is_internal, True)
            self.assertEqual(i.is_public, True)

        tmp = REQ.CPPPATH_INTERNAL  # defined "set" value
        for i in tmp:
            self.assertEqual(i.key, 'CPPPATH')
            self.assertEqual(i.is_internal, True)
            self.assertEqual(i.is_public, True)

        tmp = REQ.CPPPATH(internal=True)  # defined "set" value
        for i in tmp:
            self.assertEqual(i.key, 'CPPPATH')
            self.assertEqual(i.is_internal, True)
            self.assertEqual(i.is_public, True)

    def test_requirement_creation2(self):
        '''test requirement creation custom value'''
        tmp = REQ.FOOBAR  # defined value

        self.assertEqual(tmp.key, 'FOOBAR')
        self.assertEqual(tmp.is_internal, False)
        self.assertEqual(tmp.is_public, False)

    def test_requirement_creation3(self):
        '''test requirement creation custom value internal'''
        tmp = REQ.FOOBAR_internal  # defined value

        self.assertEqual(tmp.key, 'FOOBAR')
        self.assertEqual(tmp.is_internal, True)
        self.assertEqual(tmp.is_public, False)

        tmp = REQ.FOOBAR_INTERNAL  # defined value

        self.assertEqual(tmp.key, 'FOOBAR')
        self.assertEqual(tmp.is_internal, True)
        self.assertEqual(tmp.is_public, False)

        tmp = REQ.FOOBAR(internal=True)  # defined value

        self.assertEqual(tmp.key, 'FOOBAR')
        self.assertEqual(tmp.is_internal, True)
        self.assertEqual(tmp.is_public, False)

    def test_requirement_creation4(self):
        '''test requirement creation custom value public'''
        tmp = REQ.FOOBAR(public=True)  # defined value

        self.assertEqual(tmp.key, 'FOOBAR')
        self.assertEqual(tmp.is_internal, False)
        self.assertEqual(tmp.is_public, True)

        tmp = REQ.FOOBAR_internal(public=True)  # defined value

        self.assertEqual(tmp.key, 'FOOBAR')
        self.assertEqual(tmp.is_internal, True)
        self.assertEqual(tmp.is_public, True)

        tmp = REQ.FOOBAR_INTERNAL(public=True)  # defined value

        self.assertEqual(tmp.key, 'FOOBAR')
        self.assertEqual(tmp.is_internal, True)
        self.assertEqual(tmp.is_public, True)

        tmp = REQ.FOOBAR(internal=True, public=True)  # defined value

        self.assertEqual(tmp.key, 'FOOBAR')
        self.assertEqual(tmp.is_internal, True)
        self.assertEqual(tmp.is_public, True)

    def test_requirement_opertor(self):
        '''test REQ | operator'''
        tmp = REQ.CPPPATH | REQ.FOOBAR
        self.assertTrue(REQ.CPPPATH in tmp)
        self.assertTrue(REQ.FOOBAR in tmp)

    def test_requirement_opertor2(self):
        '''test REQ | operator 2'''
        tmp = REQ.HEADERS | REQ.FOOBAR
        self.assertTrue(REQ.CPPPATH in tmp)
        self.assertTrue(REQ.CPPDEFINES in tmp)
        self.assertTrue(REQ.FOOBAR in tmp)

    def test_requirement_opertor3(self):
        '''test REQ | operator 3'''
        tmp = REQ.HEADERS
        tmp |= REQ.FOOBAR
        self.assertTrue(REQ.CPPPATH in tmp)
        self.assertTrue(REQ.CPPDEFINES in tmp)
        self.assertTrue(REQ.FOOBAR in tmp)

    def test_requirement_value_setting_internal1(self):
        '''Test setting value outside set get value applied correctly internal1'''
        tmp = REQ.DEFAULT | REQ.CPPPATH_INTERNAL
        for i in tmp:
            if i.key == 'CPPPATH':
                self.assertEqual(i.is_internal, True)

    def test_requirement_value_setting_internal2(self):
        '''Test setting value outside set get value applied correctly internal2'''
        tmp = REQ.CPPPATH_INTERNAL | REQ.DEFAULT
        for i in tmp:
            if i.key == 'CPPPATH':
                self.assertEqual(i.is_internal, True)

    def test_requirement_value_setting_internal3(self):
        '''Test setting value outside set get value applied correctly internal1'''
        tmp = REQ.DEFAULT | REQ.CPPPATH(internal=True)
        for i in tmp:
            if i.key == 'CPPPATH':
                self.assertEqual(i.is_internal, True)

    def test_requirement_value_setting_internal4(self):
        '''Test setting value outside set get value applied correctly internal2'''
        tmp = REQ.CPPPATH(internal=True) | REQ.DEFAULT
        for i in tmp:
            if i.key == 'CPPPATH':
                self.assertEqual(i.is_internal, True)

    def test_requirement_value_setting_external1(self):
        '''Test setting value outside set get value applied correctly external1'''
        tmp = REQ.DEFAULT_INTERNAL | REQ.CPPPATH
        for i in tmp:
            if i.key == 'CPPPATH':
                self.assertEqual(i.is_internal, False)
            elif i.is_internal_forced:
                pass # if force internal we want to skip as it maybe true or false
            else:
                self.assertEqual(i.is_internal, True)

    def test_requirement_value_setting_external2(self):
        '''Test setting value outside set get value applied correctly external2'''
        tmp = REQ.CPPPATH | REQ.DEFAULT_INTERNAL
        for i in tmp:
            if i.key == 'CPPPATH':
                self.assertEqual(i.is_internal, False)
            elif i.is_internal_forced:
                pass # if force internal we want to skip as it maybe true or false
            else:
                self.assertEqual(i.is_internal, True)

    def test_requirement_value_setting_external3(self):
        '''Test setting value outside set get value applied correctly external1'''
        tmp = REQ.DEFAULT(internal=True) | REQ.CPPPATH
        for i in tmp:
            if i.key == 'CPPPATH':
                self.assertEqual(i.is_internal, False)
            elif i.is_internal_forced:
                pass # if force internal we want to skip as it maybe true or false
            else:
                self.assertEqual(i.is_internal, True)

    def test_requirement_value_setting_external4(self):
        '''Test setting value outside set get value applied correctly external2'''
        tmp = REQ.CPPPATH | REQ.DEFAULT(internal=True)
        for i in tmp:
            if i.key == 'CPPPATH':
                self.assertEqual(i.is_internal, False)
            elif i.is_internal_forced:
                pass # if force internal we want to skip as it maybe true or false
            else:
                self.assertEqual(i.is_internal, True)

    def test_state_store(self):
        '''Test if the Serialize api works'''
        tmp = REQ.CPPPATH | REQ.DEFAULT_INTERNAL
        s = tmp.Serialize()
        tmp1 = REQ()
        tmp1.Unserialize(s)

        self.assertEqual(str(tmp), str(tmp1))

    def test_intersection1(self):
        "Test that intersection return correct value"
        tmp = REQ(REQ.CPPPATH)
        result = tmp.intersection(REQ.DEFAULT)
        self.assertEqual(str(tmp), str(result))
