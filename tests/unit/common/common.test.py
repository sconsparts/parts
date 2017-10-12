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


class Test_wrap_to_string(unittest.TestCase):

    def setUp(self):
        pass

    def test_dict1(self):
        '''Test wrapping of plain dictionary'''
        obj = {'a': 1, 'b': 2}
        objWrapped = {'a': '1', 'b': '2'}
        self.assertEqual(wrap_to_string(obj), objWrapped)

    def test_dict2(self):
        '''Test wrapping of dictionary containing another dictionary'''
        obj = {'a': 1, 'b': {'c': 2, 'd': 'foo'}}
        objWrapped = {'a': '1', 'b': {'c': '2', 'd': 'foo'}}
        self.assertEqual(wrap_to_string(obj), objWrapped)

    def test_list1(self):
        '''Test wrapping of plain list'''
        obj = [1, 2, 3.45, 'foo']
        objWrapped = ['1', '2', '3.45', 'foo']
        self.assertEqual(wrap_to_string(obj), objWrapped)

    def test_list2(self):
        '''Test wrapping of list containing another list'''
        obj = [1, 2, 3.45, 'foo', ['bar', 4, 5.67]]
        objWrapped = ['1', '2', '3.45', 'foo', ['bar', '4', '5.67']]
        self.assertEqual(wrap_to_string(obj), objWrapped)

    def test_tuple1(self):
        '''Test wrapping of plain tuple'''
        obj = (1, 2, 3.45, 'foo')
        objWrapped = ('1', '2', '3.45', 'foo')
        self.assertEqual(wrap_to_string(obj), objWrapped)

    def test_tuple2(self):
        '''Test wrapping of tuple containing another tuple'''
        obj = (1, 2, 3.45, 'foo', ('bar', 4, 5.67))
        objWrapped = ('1', '2', '3.45', 'foo', ('bar', '4', '5.67'))
        self.assertEqual(wrap_to_string(obj), objWrapped)

    def test_func1(self):
        '''Test wrapping of function without keyword arguments'''
        def foo(a, b, c=None):
            pass
        obj = foo
        objWrapped = 'function foo (a,b,c)'
        self.assertEqual(wrap_to_string(obj), objWrapped)

    def test_func2(self):
        '''Test wrapping of function with keyword arguments'''
        def foo(a, b, c=None, **kw):
            pass
        obj = foo
        objWrapped = 'function foo (a,b,c,kw)'
        self.assertEqual(wrap_to_string(obj), objWrapped)

    def test_instance1(self):
        '''Test wrapping of class instance with members defined outside of class scope'''
        class A():
            pass
        aInst = A()
        aInst.a = None
        aInst.b = 1
        obj = aInst
        objWrapped = "instance of A with {'a': 'None', 'b': '1'}"
        self.assertEqual(wrap_to_string(obj), objWrapped)

    def test_instance2(self):
        '''Test wrapping of class instance with members defined inside of class scope'''
        class A():

            def __init__(self):
                self.a = None
                self.b = 1
        aInst = A()
        obj = aInst
        objWrapped = "instance of A with {'a': 'None', 'b': '1'}"
        self.assertEqual(wrap_to_string(obj), objWrapped)

    def test_class1(self):
        '''Test wrapping of class without any members'''
        class A():
            pass
        obj = A
        objWrapped = "class A {'__module__': 'common', '__doc__': 'None'}"
        self.assertEqual(wrap_to_string(obj), objWrapped)

    def test_class2(self):
        '''Test wrapping of class with __init__ member'''
        class A():

            def __init__(self):
                self.a = None
                self.b = 1
        obj = A
        objWrapped = "class A {'__module__': 'common', '__doc__': 'None', '__init__': 'function __init__ (self)'}"
        self.assertEqual(wrap_to_string(obj), objWrapped)

    def test_other1(self):
        '''Test wrapping of simple objects: int, float, string'''
        objs = [1, 2.3, 'foo']
        objsWrapped = ['1', '2.3', 'foo']
        for i in range(len(objs)):
            self.assertEqual(wrap_to_string(objs[i]), objsWrapped[i])

    def test_mixed1(self):
        '''Test wrapping of dictionary containing list, tuple and None as values'''
        obj = {'a': [1, 2.3, 'foo'], 'b': (4, 5.6, 'bar'), 'c': None}
        objWrapped = {'a': ['1', '2.3', 'foo'], 'b': ('4', '5.6', 'bar'), 'c': 'None'}
        self.assertEqual(wrap_to_string(obj), objWrapped)

    def test_cyclic1(self):
        '''Test wrapping of two dictionaries with cyclic reference to each other'''
        d0 = {}
        d1 = {'a': d0}
        d0['b'] = d1

        obj = d0
        objWrapped = {'b': {'a': '...'}}
        self.assertEqual(wrap_to_string(obj), objWrapped)

        obj = d1
        objWrapped = {'a': {'b': '...'}}
        self.assertEqual(wrap_to_string(obj), objWrapped)

    def test_cyclic2(self):
        '''Test wrapping of two lists with cyclic reference to each other'''
        l0 = []
        l1 = [l0]
        l0.append(l1)

        obj = l0
        objWrapped = [['...']]
        self.assertEqual(wrap_to_string(obj), objWrapped)

        obj = l1
        objWrapped = [['...']]
        self.assertEqual(wrap_to_string(obj), objWrapped)

    def test_cyclic3(self):
        '''Test wrapping of dictionary with cyclic reference to itself'''
        d2 = {}
        d2['a'] = d2

        obj = d2
        objWrapped = {'a': '...'}
        self.assertEqual(wrap_to_string(obj), objWrapped)

    def test_cyclic3(self):
        '''Test wrapping of dictionary where value is list with cyclic dependency to other list'''
        l0 = []
        l1 = [l0]
        l0.append(l1)
        d3 = {}
        d3['a'] = l0

        obj = d3
        objWrapped = {'a': [['...']]}
        self.assertEqual(wrap_to_string(obj), objWrapped)
