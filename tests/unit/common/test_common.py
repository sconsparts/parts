import unittest
import sys
import SCons.Script
import pytest
from parts.common import *

# Platform detection
is_win32 = sys.platform == 'win32'
is_linux = sys.platform.startswith('linux')
is_darwin = sys.platform == 'darwin'


class TestExtendUnique(unittest.TestCase):

    def setUp(self):
        pass

    def test_buildorder1(self):
        component_dependson_map = {'A': ['B', 'C'], 'B': ['D', 'E'], 'C': ['F', 'G'], 'D': [], 'E': [], 'F': [], 'G': []}
        build_list = ['A']
        for component in build_list:
            if component_dependson_map[component]:
                build_list.extend(component_dependson_map[component])
        final_list = []
        for component in build_list:
            extend_unique(final_list, build_list)
        assert final_list == ['A', 'B', 'C', 'D', 'E', 'F', 'G']

    def test_buildorder2(self):
        component_dependson_map = {'A': ['B', 'C', 'D'], 'B': ['C', 'F'], 'C': ['E', 'F'], 'D': ['B', 'E'], 'E': [], 'F': []}
        build_list = ['A']
        for component in build_list:
            if component_dependson_map[component]:
                build_list.extend(component_dependson_map[component])
        final_list = []
        for component in build_list:
            extend_unique(final_list, build_list)
        assert final_list == ['A', 'D', 'B', 'C', 'E', 'F'] or final_list == ['A', 'D', 'B', 'C', 'F', 'E']

    def test_buildorder3(self):
        component_dependson_map = {'A': ['B', 'C'], 'B': ['E', 'F'], 'C': ['G', 'E'], 'E': ['G'], 'G': [], 'F': []}
        build_list = ['A']
        for component in build_list:
            if component_dependson_map[component]:
                build_list.extend(component_dependson_map[component])
        final_list = []
        for component in build_list:
            extend_unique(final_list, build_list)
        assert final_list == ['A', 'B', 'C', 'F', 'E', 'G']


class TestExtendIfAbsent(unittest.TestCase):

    def setUp(self):
        pass

    def test_buildorder1(self):
        component_dependson_map = {'A': ['B', 'C', 'D'], 'B': ['C', 'F'], 'C': ['E', 'F'], 'D': ['B', 'E'], 'E': [], 'F': []}
        build_list = ['A']
        for component in build_list:
            if component_dependson_map[component]:
                build_list.extend(component_dependson_map[component])
        final_list = []
        for component in build_list:
            extend_if_absent(final_list, build_list)
        assert final_list == ['A', 'B', 'C', 'D', 'F', 'E']

    def test_buildorder2(self):
        component_dependson_map = {'A': ['B', 'C'], 'B': ['E', 'F'], 'C': ['G', 'E'], 'E': ['G'], 'G': [], 'F': []}
        build_list = ['A']
        for component in build_list:
            if component_dependson_map[component]:
                build_list.extend(component_dependson_map[component])
        final_list = []
        for component in build_list:
            extend_if_absent(final_list, build_list)
        assert final_list == ['A', 'B', 'C', 'E', 'F', 'G']


class TestRelPath(unittest.TestCase):

    def setUp(self):
        pass

    @pytest.mark.skipif(not is_win32, reason='Windows only')
    def test_path1(self):
        relative_path = relpath(r'C:\devel\product', r'C:\devel')
        assert relative_path == 'product'

    @pytest.mark.skipif(not is_win32, reason='Windows only')
    def test_path2(self):
        relative_path = relpath(r'C:\Documents and Settings\product',
                                r'C:\Documents and Settings')
        assert relative_path == 'product'

    def test_path3(self):
        relative_path = relpath('/opt/compiler/C', '/opt/compiler')
        assert relative_path == 'C'

    def test_path4(self):
        relative_path = relpath('/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/product',
                                '/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/opt/')
        # When given Unix-style paths, the function preserves forward slashes in output
        assert relative_path == 'opt/product'
