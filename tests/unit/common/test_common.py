import unittest
import SCons.Script
from parts.common import *


class TestExtendUnique(unittest.TestCase):

    def setUp(self):
        pass

    def test_buildorder1(self):
        component_dependson_map = {'A': ['B', 'C'], 'B': ['D', 'E'], 'C': ['F', 'G'], 'D': [], 'E': [], 'F': [], 'G': []}
        build_list = ['A']
        for component in build_list:
            if component_dependson_map[component]:
                build_list.extend(component_dependson_map[component])
                # print build_list
        final_list = []
        for component in build_list:
            extend_unique(final_list, build_list)
        # print final_list
        self.assertTrue(final_list == ['A', 'B', 'C', 'D', 'E', 'F', 'G'])  # Or many other possibilities .. Should I list all

    def test_buildorder2(self):
        component_dependson_map = {'A': ['B', 'C', 'D'], 'B': ['C', 'F'], 'C': ['E', 'F'], 'D': ['B', 'E'], 'E': [], 'F': []}
        build_list = ['A']
        for component in build_list:
            if component_dependson_map[component]:
                build_list.extend(component_dependson_map[component])
                # print build_list
        final_list = []
        for component in build_list:
            extend_unique(final_list, build_list)
        # print final_list
        self.assertTrue(final_list == ['A', 'D', 'B', 'C', 'E', 'F'] or final_list == ['A', 'D', 'B', 'C', 'F', 'E'])

    def test_buildorder3(self):
        component_dependson_map = {'A': ['B', 'C'], 'B': ['E', 'F'], 'C': ['G', 'E'], 'E': ['G'], 'G': [], 'F': []}
        build_list = ['A']
        for component in build_list:
            if component_dependson_map[component]:
                build_list.extend(component_dependson_map[component])
                # print build_list
        final_list = []
        for component in build_list:
            extend_unique(final_list, build_list)
        # print final_list
        self.assertTrue(final_list == ['A', 'B', 'C', 'F', 'E', 'G'])


class TestExtendIfAbsent(unittest.TestCase):

    def setUp(self):
        pass

    def test_buildorder1(self):
        component_dependson_map = {'A': ['B', 'C', 'D'], 'B': ['C', 'F'], 'C': ['E', 'F'], 'D': ['B', 'E'], 'E': [], 'F': []}
        build_list = ['A']
        for component in build_list:
            if component_dependson_map[component]:
                build_list.extend(component_dependson_map[component])
                # print build_list
        final_list = []
        for component in build_list:
            extend_if_absent(final_list, build_list)
        # print final_list
        self.assertTrue(final_list == ['A', 'B', 'C', 'D', 'F', 'E'])

    def test_buildorder2(self):
        component_dependson_map = {'A': ['B', 'C'], 'B': ['E', 'F'], 'C': ['G', 'E'], 'E': ['G'], 'G': [], 'F': []}
        build_list = ['A']
        for component in build_list:
            if component_dependson_map[component]:
                build_list.extend(component_dependson_map[component])
                # print build_list
        final_list = []
        for component in build_list:
            extend_if_absent(final_list, build_list)
        # print final_list
        self.assertTrue(final_list == ['A', 'B', 'C', 'E', 'F', 'G'])


class TestRelPath(unittest.TestCase):

    def setUp(self):
        pass

# @unittest.skipUnless(sys.platform.startswith('win'),"Requires windows")
# def test_path1(self):
##        relative_path = relpath('C:\devel\product','C:\devel')
# print relative_path
# self.assertEqual(relative_path,'product')
##
# @unittest.skipUnless(sys.platform.startswith('win'),"Requires windows")
# def test_path2(self):
##        relative_path = relpath('C:\Documents and Settings\product','C:\Documents and Settings')
# print relative_path
# self.assertEqual(relative_path,'product')

    def test_path3(self):
        relative_path = relpath('/opt/compiler/C', '/opt/compiler')
        # print relative_path
        self.assertEqual(relative_path, 'C')

    def test_path4(self):  # Possible Bug: it actually returns "\\" but I am giving it a Linux path
        relative_path = relpath('/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/product',
                                '/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/')
        self.assertEqual(relative_path, os.path.normpath('opt/product'))
