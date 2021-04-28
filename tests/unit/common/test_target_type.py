import unittest
import parts.target_type as target_type
from parts.reporter import PartRuntimeError


class TestTarget_base(unittest.TestCase):

    def setUp(self):
        self.target_string = 'all'
        self.string = 'build::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = None
        self.root_name = None
        self.concept = None
        self.alias = None
        self.name = None
        self.groups = []
        self.properties = {}

    def test_ambiguous(self):
        tmp = target_type.target_type(self.target_string)
        self.assertEqual(tmp.isAmbiguous, self.ambiguous)

    def test_recursive(self):
        tmp = target_type.target_type(self.target_string)
        self.assertEqual(tmp.isRecursive, self.recursive)

    def test_root_alias(self):
        tmp = target_type.target_type(self.target_string)
        self.assertEqual(tmp.RootAlias, self.root_alias)

    def test_root_name(self):
        tmp = target_type.target_type(self.target_string)
        self.assertEqual(tmp.RootName, self.root_name)

    def test_concept(self):
        tmp = target_type.target_type(self.target_string)
        self.assertEqual(tmp.Concept, self.concept)

    def test_alias(self):
        tmp = target_type.target_type(self.target_string)
        self.assertEqual(tmp.Alias, self.alias)

    def test_name(self):
        tmp = target_type.target_type(self.target_string)
        self.assertEqual(tmp.Name, self.name)

    def test_properties(self):
        tmp = target_type.target_type(self.target_string)
        self.assertEqual(tmp.Properties, self.properties)

    def test_groups(self):
        tmp = target_type.target_type(self.target_string)
        self.assertEqual(tuple(tmp.Groups), tuple(self.groups))

    def test_str(self):
        tmp = target_type.target_type(self.target_string)
        self.assertEqual(str(tmp), self.string)


class TestTarget_all(TestTarget_base):

    def setUp(self):
        self.target_string = 'all'
        self.string = 'build::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = None
        self.root_name = None
        self.concept = None
        self.alias = None
        self.name = None
        self.groups = []
        self.properties = {}


class TestTarget_concept1(TestTarget_base):

    def setUp(self):
        self.target_string = 'build::'
        self.string = 'build::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = None
        self.root_name = None
        self.concept = "build"
        self.alias = None
        self.name = None
        self.groups = []
        self.properties = {}


class TestTarget_concept2(TestTarget_base):

    def setUp(self):
        self.target_string = 'utest::'
        self.string = 'utest::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = None
        self.root_name = None
        self.concept = "utest"
        self.alias = None
        self.name = None
        self.groups = []
        self.properties = {}


class TestTarget_concept3(TestTarget_base):

    def setUp(self):
        self.target_string = 'run_utest::'
        self.string = 'run_utest::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = None
        self.root_name = None
        self.concept = "run_utest"
        self.alias = None
        self.name = None
        self.groups = []
        self.properties = {}


class TestTarget_special1(TestTarget_base):

    def setUp(self):
        self.target_string = 'name::'
        self.string = 'build::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = None
        self.root_name = None
        self.concept = None
        self.alias = None
        self.name = None
        self.groups = []
        self.properties = {}


class TestTarget_special2(TestTarget_base):

    def setUp(self):
        self.target_string = 'alias::'
        self.string = 'build::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = None
        self.root_name = None
        self.concept = None
        self.alias = None
        self.name = None
        self.groups = []
        self.properties = {}


class TestTarget_special3(TestTarget_base):

    def setUp(self):
        self.target_string = 'name::::'
        self.string = 'build::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = None
        self.root_name = None
        self.concept = None
        self.alias = None
        self.name = None
        self.groups = []
        self.properties = {}


class TestTarget_special4(TestTarget_base):

    def setUp(self):
        self.target_string = 'alias::::'
        self.string = 'build::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = None
        self.root_name = None
        self.concept = None
        self.alias = None
        self.name = None
        self.groups = []
        self.properties = {}


class TestTarget_implied_name1(TestTarget_base):

    def setUp(self):
        self.target_string = 'build'
        self.string = 'name::build'
        self.ambiguous = True
        self.recursive = False
        self.root_alias = None
        self.root_name = 'build'
        self.concept = None
        self.alias = None
        self.name = 'build'
        self.groups = []
        self.properties = {}


class TestTarget_implied_name2(TestTarget_base):

    def setUp(self):
        self.target_string = 'utest'
        self.string = 'name::utest'
        self.ambiguous = True
        self.recursive = False
        self.root_alias = None
        self.root_name = 'utest'
        self.concept = None
        self.alias = None
        self.name = 'utest'
        self.groups = []
        self.properties = {}


class TestTarget_implied_name3(TestTarget_base):

    def setUp(self):
        self.target_string = 'run_utest'
        self.string = 'name::run_utest'
        self.ambiguous = True
        self.recursive = False
        self.root_alias = None
        self.root_name = 'run_utest'
        self.concept = None
        self.alias = None
        self.name = 'run_utest'
        self.groups = []
        self.properties = {}


class TestTarget_implied_name4(TestTarget_base):

    def setUp(self):
        self.target_string = 'alias'
        self.string = 'name::alias'
        self.ambiguous = True
        self.recursive = False
        self.root_alias = None
        self.root_name = 'alias'
        self.concept = None
        self.alias = None
        self.name = 'alias'
        self.groups = []
        self.properties = {}


class TestTarget_implied_name5(TestTarget_base):

    def setUp(self):
        self.target_string = 'name'
        self.string = 'name::name'
        self.ambiguous = True
        self.recursive = False
        self.root_alias = None
        self.root_name = 'name'
        self.concept = None
        self.alias = None
        self.name = 'name'
        self.groups = []
        self.properties = {}


class TestTarget_implied_name6(TestTarget_base):

    def setUp(self):
        self.target_string = 'name@k:v@k1:1,2,3,4@k3:hello'
        self.string = 'name::name@k:v@k1:1,2,3,4@k3:hello'
        self.ambiguous = False
        self.recursive = False
        self.root_alias = None
        self.root_name = 'name'
        self.concept = None
        self.alias = None
        self.name = 'name'
        self.groups = []
        self.properties = {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3', '4']}


class TestTarget_implied_name7(TestTarget_base):

    def setUp(self):
        self.target_string = 'alias@k:v@k1:1,2,3,4@k3:hello'
        self.string = 'name::alias@k:v@k1:1,2,3,4@k3:hello'
        self.ambiguous = False
        self.recursive = False
        self.root_alias = None
        self.root_name = 'alias'
        self.concept = None
        self.alias = None
        self.name = 'alias'
        self.groups = []
        self.properties = {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3', '4']}


class TestTarget_alias1(TestTarget_base):

    def setUp(self):
        self.target_string = 'alias::foo'
        self.string = 'alias::foo'
        self.ambiguous = False
        self.recursive = False
        self.root_alias = 'foo'
        self.root_name = None
        self.concept = None
        self.alias = 'foo'
        self.name = None
        self.groups = []
        self.properties = {}


class TestTarget_alias2(TestTarget_base):

    def setUp(self):
        self.target_string = 'alias::foo.boo'
        self.string = 'alias::foo.boo'
        self.ambiguous = False
        self.recursive = False
        self.root_alias = 'foo'
        self.root_name = None
        self.concept = None
        self.alias = 'foo.boo'
        self.name = None
        self.groups = []
        self.properties = {}


class TestTarget_alias3(TestTarget_base):

    def setUp(self):
        self.target_string = 'build::alias::foo'
        self.string = 'build::alias::foo'
        self.ambiguous = False
        self.recursive = False
        self.root_alias = 'foo'
        self.root_name = None
        self.concept = "build"
        self.alias = 'foo'
        self.name = None
        self.groups = []
        self.properties = {}


class TestTarget_alias4(TestTarget_base):

    def setUp(self):
        self.target_string = 'utest::alias::foo'
        self.string = 'utest::alias::foo'
        self.ambiguous = False
        self.recursive = False
        self.root_alias = 'foo'
        self.root_name = None
        self.concept = "utest"
        self.alias = 'foo'
        self.name = None
        self.groups = []
        self.properties = {}


class TestTarget_alias5(TestTarget_base):

    def setUp(self):
        self.target_string = 'alias::foo::'
        self.string = 'alias::foo::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = 'foo'
        self.root_name = None
        self.concept = None
        self.alias = 'foo'
        self.name = None
        self.groups = []
        self.properties = {}


class TestTarget_alias6(TestTarget_base):

    def setUp(self):
        self.target_string = 'alias::foo.boo::'
        self.string = 'alias::foo.boo::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = 'foo'
        self.root_name = None
        self.concept = None
        self.alias = 'foo.boo'
        self.name = None
        self.groups = []
        self.properties = {}


class TestTarget_alias7(TestTarget_base):

    def setUp(self):
        self.target_string = 'build::alias::foo::'
        self.string = 'build::alias::foo::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = 'foo'
        self.root_name = None
        self.concept = "build"
        self.alias = 'foo'
        self.name = None
        self.groups = []
        self.properties = {}


class TestTarget_alias8(TestTarget_base):

    def setUp(self):
        self.target_string = 'utest::alias::foo::'
        self.string = 'utest::alias::foo::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = 'foo'
        self.root_name = None
        self.concept = "utest"
        self.alias = 'foo'
        self.name = None
        self.groups = []
        self.properties = {}


class TestTarget_name1(TestTarget_base):

    def setUp(self):
        self.target_string = 'name::foo'
        self.string = 'name::foo'
        self.ambiguous = False
        self.recursive = False
        self.root_alias = None
        self.root_name = 'foo'
        self.concept = None
        self.alias = None
        self.name = 'foo'
        self.groups = []
        self.properties = {}


class TestTarget_name2(TestTarget_base):

    def setUp(self):
        self.target_string = 'name::foo.boo'
        self.string = 'name::foo.boo'
        self.ambiguous = False
        self.recursive = False
        self.root_alias = None
        self.root_name = 'foo'
        self.concept = None
        self.alias = None
        self.name = 'foo.boo'
        self.groups = []
        self.properties = {}


class TestTarget_name3(TestTarget_base):

    def setUp(self):
        self.target_string = 'build::name::foo'
        self.string = 'build::name::foo'
        self.ambiguous = False
        self.recursive = False
        self.root_alias = None
        self.root_name = 'foo'
        self.concept = "build"
        self.alias = None
        self.name = 'foo'
        self.groups = []
        self.properties = {}


class TestTarget_name4(TestTarget_base):

    def setUp(self):
        self.target_string = 'utest::name::foo'
        self.string = 'utest::name::foo'
        self.ambiguous = False
        self.recursive = False
        self.root_alias = None
        self.root_name = 'foo'
        self.concept = "utest"
        self.alias = None
        self.name = 'foo'
        self.groups = []
        self.properties = {}


class TestTarget_name5(TestTarget_base):

    def setUp(self):
        self.target_string = 'name::foo::'
        self.string = 'name::foo::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = None
        self.root_name = 'foo'
        self.concept = None
        self.alias = None
        self.name = 'foo'
        self.groups = []
        self.properties = {}


class TestTarget_name6(TestTarget_base):

    def setUp(self):
        self.target_string = 'name::foo.boo::'
        self.string = 'name::foo.boo::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = None
        self.root_name = 'foo'
        self.concept = None
        self.alias = None
        self.name = 'foo.boo'
        self.groups = []
        self.properties = {}


class TestTarget_name7(TestTarget_base):

    def setUp(self):
        self.target_string = 'build::name::foo::'
        self.string = 'build::name::foo::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = None
        self.root_name = 'foo'
        self.concept = "build"
        self.alias = None
        self.name = 'foo'
        self.groups = []
        self.properties = {}


class TestTarget_name8(TestTarget_base):

    def setUp(self):
        self.target_string = 'utest::name::foo::'
        self.string = 'utest::name::foo::'
        self.ambiguous = False
        self.recursive = True
        self.root_alias = None
        self.root_name = 'foo'
        self.concept = "utest"
        self.alias = None
        self.name = 'foo'
        self.groups = []
        self.properties = {}


class TestParseTarget(unittest.TestCase):

    def setUp(self):
        pass

    def test_parse_all(self):
        '''Testing parsing of concept all'''
        tmp = target_type._parse_target("all")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': True})

    def test_parse_concept1(self):
        '''Testing parsing of concept build::'''
        tmp = target_type._parse_target("build::")
        self.assertEqual(tmp, {'_concept': 'build', '_section': 'build', '_recursive': True})

    def test_parse_concept2(self):
        '''Testing parsing of concept utest::'''
        tmp = target_type._parse_target("utest::")
        self.assertEqual(tmp, {'_concept': 'utest', '_section': 'unit_test', '_recursive': True})

    def test_parse_concept3(self):
        '''Testing parsing of concept run_utest:: maps to utest::'''
        tmp = target_type._parse_target("run_utest::")
        self.assertEqual(tmp, {'_concept': 'run_utest', '_section': 'unit_test', '_recursive': True})

    def test_parse_concept_special1(self):
        '''Testing parsing of concept name::'''
        tmp = target_type._parse_target("name::")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': True})

    def test_parse_concept_special2(self):
        '''Testing parsing of concept alias::'''
        tmp = target_type._parse_target("alias::")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': True})

    def test_parse_concept_special3(self):
        '''Testing parsing of concept name::::'''
        tmp = target_type._parse_target("name::::")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': True})

    def test_parse_concept_special4(self):
        '''Testing parsing of concept alias::::'''
        tmp = target_type._parse_target("alias::::")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': True})

    def test_parse_concept_as_implied_name1(self):
        '''Testing parsing of concept build as an name'''
        tmp = target_type._parse_target("build")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': False, '_name': 'build', '_ambiguous': True})

    def test_parse_concept_as_implied_name2(self):
        '''Testing parsing of concept utest as an name'''
        tmp = target_type._parse_target("utest")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': False, '_name': 'utest', '_ambiguous': True})

    def test_parse_concept_as_implied_name3(self):
        '''Testing parsing of concept run_utest as an name'''
        tmp = target_type._parse_target("run_utest")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': False, '_name': 'run_utest', '_ambiguous': True})

    def test_parse_concept_as_implied_name4(self):
        '''Testing parsing of 'alias' as an name'''
        tmp = target_type._parse_target("alias")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': False, '_name': 'alias', '_ambiguous': True})

    def test_parse_concept_as_implied_name5(self):
        '''Testing parsing of concept name as an name'''
        tmp = target_type._parse_target("name")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': False, '_name': 'name', '_ambiguous': True})

    def test_parse_concept_as_implied_name5(self):
        '''Testing parsing of concept name<properties> as an name'''
        tmp = target_type._parse_target("name@k:v@k1:1,2,3,4@k3:hello")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': False, '_name': 'name',
                               '_properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3', '4']}})

    def test_parse_concept_as_implied_name6(self):
        '''Testing parsing of concept alias<properties> as an name'''
        tmp = target_type._parse_target("alias@k:v@k1:1,2,3,4@k3:hello")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': False, '_name': 'alias',
                               '_properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3', '4']}})

    def test_parse_alias1(self):
        '''Testing parsing of alias::foo'''
        tmp = target_type._parse_target("alias::foo")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': False, '_alias': 'foo'})

    def test_parse_alias2(self):
        '''Testing parsing of alias::foo.boo'''
        tmp = target_type._parse_target("alias::foo.boo")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': False, '_alias': 'foo.boo'})

    def test_parse_alias3(self):
        '''Testing parsing of build::alias::foo'''
        tmp = target_type._parse_target("build::alias::foo")
        self.assertEqual(tmp, {'_concept': 'build', '_section': 'build', '_recursive': False, '_alias': 'foo'})

    def test_parse_alias4(self):
        '''Testing parsing of utest::alias::foo'''
        tmp = target_type._parse_target("utest::alias::foo")
        self.assertEqual(tmp, {'_concept': 'utest', '_section': 'unit_test', '_recursive': False, '_alias': 'foo'})

    def test_parse_alias5(self):
        '''Testing parsing of alias::foo::'''
        tmp = target_type._parse_target("alias::foo::")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': True, '_alias': 'foo'})

    def test_parse_alias6(self):
        '''Testing parsing of alias::foo.boo::'''
        tmp = target_type._parse_target("alias::foo.boo::")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': True, '_alias': 'foo.boo'})

    def test_parse_alias7(self):
        '''Testing parsing of build::alias::foo::'''
        tmp = target_type._parse_target("build::alias::foo::")
        self.assertEqual(tmp, {'_concept': 'build', '_section': 'build', '_recursive': True, '_alias': 'foo'})

    def test_parse_alias8(self):
        '''Testing parsing of utest::alias::foo::'''
        tmp = target_type._parse_target("utest::alias::foo::")
        self.assertEqual(tmp, {'_concept': 'utest', '_section': 'unit_test', '_recursive': True, '_alias': 'foo'})

    def test_parse_name1(self):
        '''Testing parsing of name::foo'''
        tmp = target_type._parse_target("name::foo")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': False, '_name': 'foo', '_properties': {}})

    def test_parse_name2(self):
        '''Testing parsing of name::foo.boo'''
        tmp = target_type._parse_target("name::foo.boo")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': False, '_name': 'foo.boo', '_properties': {}})

    def test_parse_name3(self):
        '''Testing parsing of build::name::foo'''
        tmp = target_type._parse_target("build::name::foo")
        self.assertEqual(tmp, {'_concept': 'build', '_section': 'build', '_recursive': False, '_name': 'foo', '_properties': {}})

    def test_parse_name4(self):
        '''Testing parsing of utest::name::foo'''
        tmp = target_type._parse_target("utest::name::foo")
        self.assertEqual(tmp, {'_concept': 'utest', '_section': 'unit_test', '_recursive': False, '_name': 'foo', '_properties': {}})

    def test_parse_name5(self):
        '''Testing parsing of utest::foo'''
        tmp = target_type._parse_target("utest::foo")
        self.assertEqual(tmp, {'_concept': 'utest', '_section': 'unit_test', '_recursive': False, '_name': 'foo', '_properties': {}})

    def test_parse_name6(self):
        '''Testing parsing of name::foo'''
        tmp = target_type._parse_target("name::foo::")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': True, '_name': 'foo', '_properties': {}})

    def test_parse_name7(self):
        '''Testing parsing of name::foo.boo::'''
        tmp = target_type._parse_target("name::foo.boo::")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': True, '_name': 'foo.boo', '_properties': {}})

    def test_parse_name8(self):
        '''Testing parsing of build::name::foo::'''
        tmp = target_type._parse_target("build::name::foo::")
        self.assertEqual(tmp, {'_concept': 'build', '_section': 'build', '_recursive': True, '_name': 'foo', '_properties': {}})

    def test_parse_name8(self):
        '''Testing parsing of utest::name::foo::'''
        tmp = target_type._parse_target("utest::name::foo::")
        self.assertEqual(tmp, {'_concept': 'utest', '_section': 'unit_test', '_recursive': True, '_name': 'foo', '_properties': {}})

    def test_parse_name10(self):
        '''Testing parsing of utest::foo::'''
        tmp = target_type._parse_target("utest::foo::")
        self.assertEqual(tmp, {'_concept': 'utest', '_section': 'unit_test', '_recursive': True, '_name': 'foo', '_properties': {}})

    def test_parse_name_properties1(self):
        '''Testing parsing of utest::name::c@k:v@k1:1,2,3,4@k3:hello::'''
        tmp = target_type._parse_target("utest::name::c@k:v@k1:1,2,3,4@k3:hello::")
        self.assertEqual(tmp, {'_concept': 'utest', '_section': 'unit_test', '_recursive': True, '_name': 'c',
                               '_properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3', '4']}})

    def test_parse_name_properties2(self):
        '''Testing parsing of utest::name::c@k:v@k1:1,2,3,4@k3:hello'''
        tmp = target_type._parse_target("utest::name::c@k:v@k1:1,2,3,4@k3:hello")
        self.assertEqual(tmp, {'_concept': 'utest', '_section': 'unit_test', '_recursive': False, '_name': 'c',
                               '_properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3', '4']}})

    def test_parse_name_properties3(self):
        '''Testing parsing of name::c@k:v@k1:1,2,3,4@k3:hello::'''
        tmp = target_type._parse_target("name::c@k:v@k1:1,2,3,4@k3:hello::")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': True, '_name': 'c',
                               '_properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3', '4']}})

    def test_parse_name_properties4(self):
        '''Testing parsing of name::c@k:v@k1:1,2,3,4@k3:hello'''
        tmp = target_type._parse_target("name::c@k:v@k1:1,2,3,4@k3:hello")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': False, '_name': 'c',
                               '_properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3', '4']}})

    def test_parse_name_properties5(self):
        '''Testing parsing of c@k:v@k1:1,2,3,4@k3:hello::'''
        tmp = target_type._parse_target("c@k:v@k1:1,2,3,4@k3:hello::")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': True, '_name': 'c',
                               '_properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3', '4']}})

    def test_parse_name_properties6(self):
        '''Testing parsing of c@k:v@k1:1,2,3,4@k3:hello'''
        tmp = target_type._parse_target("c@k:v@k1:1,2,3,4@k3:hello")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': False, '_name': 'c',
                               '_properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3', '4']}})

    def test_parse_name_properties7(self):
        '''Testing parsing of c@k:v@k1:1,2,3,4@k3:hello::a1,a2,b3::'''
        tmp = target_type._parse_target("c@k:v@k1:1,2,3,4@k3:hello::a1,a2,b3::")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': True, '_name': 'c', '_groups': [
                         'a1', 'a2', 'b3'], '_properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3', '4']}})

    def test_parse_name_properties8(self):
        '''Testing parsing of c@k:v@k1:1,2,3,4@k3:hello::a1,a2,b3'''
        tmp = target_type._parse_target("c@k:v@k1:1,2,3,4@k3:hello::a1,a2,b3")
        self.assertEqual(tmp, {'_section': 'build', '_recursive': False, '_name': 'c', '_groups': [
                         'a1', 'a2', 'b3'], '_properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3', '4']}})

    def test_special1(self):
        '''Testing parsing of utest::::test'''
        tmp = target_type._parse_target("utest::::test")
        self.assertEqual(tmp, {'_concept': 'utest', '_section': 'unit_test', '_recursive': False, '_groups': ['test']})

    def test_special2(self):
        '''Testing parsing of utest::alias::::test'''
        tmp = target_type._parse_target("utest::alias::::test")
        self.assertEqual(tmp, {'_concept': 'utest', '_section': 'unit_test', '_recursive': False, '_groups': ['test']})

    def test_special3(self):
        '''Testing parsing of utest::name::::test'''
        tmp = target_type._parse_target("utest::name::::test")
        self.assertEqual(tmp, {'_concept': 'utest', '_section': 'unit_test', '_recursive': False, '_groups': ['test']})

    def test_special4(self):
        '''Testing parsing of utest::::test::'''
        tmp = target_type._parse_target("utest::::test::")
        self.assertEqual(tmp, {'_concept': 'utest', '_section': 'unit_test', '_recursive': True, '_groups': ['test']})

    def test_special5(self):
        '''Testing parsing of utest::alias::::test::'''
        tmp = target_type._parse_target("utest::alias::::test::")
        self.assertEqual(tmp, {'_concept': 'utest', '_section': 'unit_test', '_recursive': True, '_groups': ['test']})

    def test_special6(self):
        '''Testing parsing of utest::name::::test::'''
        tmp = target_type._parse_target("utest::name::::test::")
        self.assertEqual(tmp, {'_concept': 'utest', '_section': 'unit_test', '_recursive': True, '_groups': ['test']})

    def test_special7(self):
        '''Testing parsing of build::::'''
        tmp = target_type._parse_target("build::::")
        self.assertEqual(tmp, {'_concept': 'build', '_section': 'build', '_recursive': True})

    def test_special8(self):
        '''Testing parsing of build::alias::::'''
        tmp = target_type._parse_target("build::alias::::")
        self.assertEqual(tmp, {'_concept': 'build', '_section': 'build', '_recursive': True})

    def test_special9(self):
        '''Testing parsing of build::name::::'''
        tmp = target_type._parse_target("build::name::::")
        self.assertEqual(tmp, {'_concept': 'build', '_section': 'build', '_recursive': True})

    def test_special10(self):
        '''Testing parsing of build::::::'''
        tmp = target_type._parse_target("build::::::")
        self.assertEqual(tmp, {'_concept': 'build', '_section': 'build', '_recursive': True})

    def test_special11(self):
        '''Testing parsing of build::alias::::::'''
        tmp = target_type._parse_target("build::alias::::::")
        self.assertEqual(tmp, {'_concept': 'build', '_section': 'build', '_recursive': True})

    def test_special12(self):
        '''Testing parsing of build::name::::::'''
        tmp = target_type._parse_target("build::name::::::")
        self.assertEqual(tmp, {'_concept': 'build', '_section': 'build', '_recursive': True})

    def test_special_error1(self):
        '''Testing parsing of build::name::n::g:::: exception expected'''
        try:
            tmp = target_type._parse_target("build::name::n::g::::")
        except PartRuntimeError as e:
            self.assertTrue(True)
            return
        self.assertTrue(False)

    def test_special_error2(self):
        '''Testing parsing of build:::::::: exception expected'''
        try:
            tmp = target_type._parse_target("build::::::::")
        except PartRuntimeError as e:
            self.assertTrue(True)
            return
        self.assertTrue(False)
