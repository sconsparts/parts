from __future__ import absolute_import, division, print_function

import hashlib
import itertools
import sys
from builtins import filter

import _thread
from past.builtins import cmp

import parts.api as api
import parts.common as common
import parts.core.util as util
import parts.datacache as datacache
import parts.functors as functors
import parts.glb as glb
import parts.mappers as mappers
import parts.pnode.dependent_info as dependent_info
import parts.pnode.pnode as pnode
import parts.pnode.pnode_manager as pnode_manager
import parts.pnode.section_info as section_info
import parts.target_type as target_type
import SCons.Node


class section(pnode.pnode):
    """description of class"""
    __slots__ = [
        '_ID',
        '__depends',  # what we depend on directly (ie explictly), as list (order needed) of ComponentRef objects
        '__full_depends',  # what depend on directly and indirectly

        '__exports',  # value we will export
        '__export_as_depends',  # list of values exported item to map as a depends node, when they are referenced in a dependson call

        # '__build_context_files', # File that contain code for the builder (or best guess)
        '__target_nodes',  # target node for this section
        '__source_nodes',  # Source node for this section
        '__installed_files',  # anything that gets installed for packaging.


        '__pobj',  # reference to the part containing this section.
        '__env',  # the environment for the given section (cloned from Parts object)
        '__user_env_diff',
        '__cache'
    ]

    @property
    def _cache(self):
        try:
            return self.__cache
        except AttributeError:
            self.__cache = result = dict()
            return result

    def __init__(self, pobj=None, ID=None):

        if ID:
            self._ID = ID

        if pobj:
            self.__pobj = pobj

        super(section, self).__init__()

    def _setup_(self, pobj, env=None, *lst, **kw):
        self.__pobj = pobj
        if env:
            self.__env = env
        else:
            self.__env = self.__pobj.Env.Clone()
        self.__env['PART_SECTION'] = self.Name

    __to_delete = (
        '_section__depends',
        '_section__full_depends',

        '_section__exports',
        '_section__export_as_depends',

        '_section__source_nodes',
        '_section__target_nodes',
        '_section__installed_files',
        '_section__user_env_diff',
        '_section_cache',
    )

    def Reset(self):
        ''' reset cached state of section'''
        for item in self.__to_delete:
            try:
                delattr(self, item)
            except AttributeError:
                pass

    @property
    def Name(self):
        raise NotImplementedError

    @property
    def Exports(self):  # mutable
        try:
            return self.__exports
        except AttributeError:
            self.__exports = result = dict()
            return result

    @property
    def ExportAsDepends(self):
        try:
            return self.__export_as_depends
        except AttributeError:
            self.__export_as_depends = result = list()
            return result

    @property
    def Targets(self):
        try:
            return self.__target_nodes
        except AttributeError:
            self.__target_nodes = result = list()
            return result

    @property
    def Sources(self):
        try:
            return self.__source_nodes
        except AttributeError:
            self.__source_nodes = result = list()
            return result

    @property
    def InstalledFiles(self):
        try:
            return self.__installed_files
        except AttributeError:
            self.__installed_files = result = set()
            return result

    @property
    def Depends(self):
        try:
            return self.__depends
        except AttributeError:
            self.__depends = result = list()
            return result

    @Depends.setter
    def Depends(self, val):
        common.extend_if_absent(self.Depends, common.make_list(val))

    @property
    def AlwaysBuild(self):
        return self._cache.get("always_build", False)

    @AlwaysBuild.setter
    def AlwaysBuild(self, val):
        self._cache["always_build"] = val

    @property
    def FullDepends(self):
        try:
            return self.__full_depends
        except AttributeError:
            self.__full_depends = result = list()
            return result

    @property
    def Part(self):
        try:
            return self.__pobj
        except AttributeError:
            return None

    @property
    def Env(self):
        try:
            return self.__env
        except AttributeError:
            self.__env = result = self.Part.Env.Clone()
            return result

    @property
    def UserEnvDiff(self):
        try:
            return self.__user_env_diff
        except AttributeError:
            self.__user_env_diff = result = dict()
            return result

    def gen_system_concept_set(self):
        concept_set = set([])

        for concept in ("build", "utest", "run_utest"):
            pobj = self.__pobj
            while pobj:
                alias_str = '{0}::alias::{1}'.format(concept, pobj.alias)
                alias_str_r = '{0}::'.format(alias_str)
                concept_set.add(alias_str)
                concept_set.add(alias_str_r)
                pobj = pobj.Parent
            concept_str = '{0}::'.format(concept)
            concept_set.add(concept_str)

        return concept_set

    def filter_system_nodes(self, nodes):
        # a system node:
        #   needs to be an alias node and
        #   equal to any known concept mapping values
        #       alias_str or alias_str_r or equal to the concept
        #  This is the base Alias for a given Part

        # should be cleaned up once allow users to define there own concepts...
        # get "known" concepts and makes expect strings

        concept_set = self.gen_system_concept_set()
        # the startwith runutest:: is a workaround till we deal with sections better

        def is_system(node):
            return isinstance(node, SCons.Node.Alias.Alias) and\
                (node.ID in concept_set or node.ID.startswith("run_utest::"))

        return [n for n in nodes if not is_system(n)]

    @property
    def Alias(self):
        try:
            self._cache["alias"]
        except KeyError:
            alias_str = '{0}::alias::{1}'.format(self.Name, self.__pobj.Alias)
            self._cache["alias"] = self.__env.Alias(alias_str)
        return self._cache["alias"]

    def TopLevelTargets(self):
        '''
        returns the top level targets.. ie the targets that are not children
        of the other targets 
        '''
        top_level = []
        # make copy
        test_targets = set(self.filter_system_nodes(self.Targets))
        targets = set(test_targets)
        # api.output.verbose_msgf(
        # ['top-level-mapping'],
        # "Filtered targets nodes for '{}':\n{}", self.ID, common.DelayVariable(lambda: [n.ID for n in targets]))
        # filter some special targets
        alias_str = '{0}::alias::{1}'.format(self.Name, self.__pobj.Alias)
        rm_targets = set(self.__env.Alias(alias_str))

        # for each target
        for trg in targets:
            for test_target in test_targets:
                # test to see if this target is known to not be a top level
                if test_target in rm_targets:
                    # if so continue
                    continue
                if trg.is_child(test_target):
                    rm_targets.add(test_target)
                if test_target.is_child(trg):
                    # trg is under the test trg
                    # add to remove set
                    rm_targets.add(trg)

        # filter all nodes that are not in rm set
        ret = [t for t in test_targets if t not in rm_targets]
        api.output.verbose_msgf(
            ['top-level-mapping'],
            "Mapping nodes to '{}':\n{}", self.ID, common.DelayVariable(lambda: [n.ID for n in ret]))
        return ret

    def _map_target(self, node, subtarget=None):

        # if we have a sub-target, we will want to map it to the top-level target
        if subtarget:
            alias_str = '{0}::alias::{1}::{2}'.format(self.Name, self.__pobj.Alias, subtarget)
            node = self.__env.Alias(alias_str, node)

        alias_str = '{0}::alias::{1}'.format(self.Name, self.__pobj.Alias)
        self.__env.Alias(alias_str, node)

    def _map_targets(self):
        '''
        Here we map all known target files that happen in this component
        to the alias value, to ensure that it is built in case there are actions
        that are no mapped correctly to some action that is mapped to the alias
        such as and sdk or install action
        '''

        # This is the base Alias for a given Part
        alias_str = '{0}::alias::{1}'.format(self.Name, self.__pobj.Alias)
        alias_str_r = '{0}::'.format(alias_str)

        ########
        # This is being done differently via a toplevel target mapping which I think while be better
        # # This magic here find all Alias targets that got defined, and if there are in a certain format,
        # # they get mapped as a dependancy to the primary alias. This allows us to make "groups" aliases
        # # so we can depend on a set of node, such as all the include file, or lib files of a part without
        # # depending on every piece it would build.
        # # build::alias::foo
        # #def map_alias(obj):
        #     # needs to be an alias node
        #     # and it should start with the alias_str
        #     # but it should not equal the alias_str or alias_str_r
        #     #return isinstance(obj, SCons.Node.Alias.Alias) and\
        #         #obj.ID.startswith(alias_str) and\
        #         #obj.ID != alias_str and\
        #         #obj.ID != alias_str_r

        # #a = self.__env.Alias(alias_str, [n for n in self.Targets if map_alias(n)])

        ####################
        # current changes has this function only mapping top level alias targets
        # the alias_str will be mapped via the top level logic after the part is loaded
        # ideall we could map this after the part load with the top level target mapping
        a = self.__env.Alias(alias_str)
        # build::alias::foo -> build::alias::foo::
        a1 = self.__env.Alias(alias_str_r, a)

        # map build::alias::foo.sub1:: -> build::alias::foo::
        if not self.Part.isRoot:  # ie we have a parent
            # build::alias::foo.sub:: -> build::alias::foo::
            self.__env.Alias('{0}${{ALIAS_SEPARATOR}}${{PART_ALIAS_CONCEPT}}{1}::'.format(self.Name, self.Part.Parent.Alias), a1)
        # else:
        # build::alias::foo -> build::alias::foo:: -> build::
        self.__env.Alias("{0}${{ALIAS_SEPARATOR}}".format(self.Name), a1)
        # add call back for latter full mapping of build context
        functors.map_build_context(self.Part)()

    def ESigs(self):

        def replace_nodes(lst):
            newval = []
            for i in lst:
                if isinstance(i, SCons.Node.FS.Base):
                    newval.append(i.ID)
                elif util.isList(i):
                    newval.append(replace_nodes(i))
                elif i is None or i == [] or i == '':
                    pass
                else:
                    newval.append(i)
            return newval

        try:
            return self._cache['esigs']
        except KeyError:
            esig = hashlib.md5()
            # we expand the values here to reduce processing needs latter
            # the the reason we would store this is to speed up build latter
            # ideally this only needs to be expanded in cases of the classic format
            # or cases in which the user added such value to be exported

            export_csig = {}
            for key, value in list(self.Exports.items()):
                if util.isList(value):
                    # We want to modify self.Exports but leave the Env intact
                    # so we call subst list with recurse == True
                    mappers.sub_lst(self.Env, value, _thread.get_ident(), recurse=True)
                    # mappers.sub_lst call may modify exports therefore we cannot use 'value' here
                    if not any(self.Exports[key]):
                        del self.__exports[key]
                        continue
                else:
                    if util.isString(value) and '$' in value:
                        tmp = self.Env.subst(value, conv=lambda x: x)
                        if not tmp:
                            del self.__exports[key]
                            continue
                    elif not value:
                        del self.__exports[key]
                        continue
                try:

                    md5 = hashlib.md5()
                    md5.update(common.get_content(self.__exports[key]))
                    tmp = md5.hexdigest().encode()
                    esig.update(tmp)
                    export_csig[key] = tmp
                except KeyError:
                    pass

            self._cache['esigs'] = export_csig
            self._cache['esig'] = esig.hexdigest()

        return self._cache['esigs']

    def ESig(self):
        try:
            return self._cache['esig']
        except KeyError:
            self.ESigs()
        return self._cache['esig']

    def LoadStoredInfo(self):
        tmp = glb.pnodes.GetStoredPNodeInfo(self)
        if tmp.PartID:  # quick sanity check that this is good data
            return tmp
        return None

    def GenerateStoredInfo(self):
        info = section_info.section_info()

        info.PartID = self.Part.ID
        info.Name = self.Name

        info.ESigs = self.ESigs()
        info.ESig = self.ESig()
        info.Exports = self.Exports
        if self.InstalledFiles:
            info.InstalledFiles = (
                (node.ID, getattr(node.attributes, 'package', {}))
                for node in self.InstalledFiles)

        # data about what this depends on we want the direct depend here
        # as this will allow us to speed up incremential build latter
        tmp = []
        # to get the dependance sig
        for d in self.Depends:
            tmp.append(
                dependent_info.dependent_info(d)
            )

        info.UserEnvDiff = self.UserEnvDiff
        info.DependsOn = tmp
        # these are items that are exported, and noted as a map_as_depends in ExportItem()
        info.ExportedRequirements = self.ExportAsDepends

        return info

    def LoadFromCache(self):
        info = self.Stored
        # get out owning part
        self.__pobj = info.Part
        self.__env = self.__pobj.Env.Clone()
        self.__env['PART_SECTION'] = self.Name
        user_env_diff = info.UserEnvDiff
        if user_env_diff:
            self.__user_env_diff = dict(user_env_diff)
            self.__env.Replace(**self.UserEnvDiff)
        # import the values we export
        # We assume these are fully resolved so we don't need to get any data from anything this
        # section would have depended on
        exports = info.Exports
        if exports:
            self.__exports = dict(exports)

        # need to map these items as Aliases
        export_as_depends = info.ExportedRequirements
        if export_as_depends:
            self.__export_as_depends = list(export_as_depends)
            for export in export_as_depends:
                try:
                    self.__env.Alias("{0}::alias::{1}::{2}".format(self.Name, self.__pobj.Alias, export),
                                     self.Exports[export])
                except KeyError:
                    api.output.verbose_msgf(['cache_load_warning'],
                                            "{0} was not found in the exports dictionary. Mapping value of []", export)
                    self.__env.Alias("{0}::alias::{1}::{2}".format(self.Name, self.__pobj.Alias, export), [])
        cached = info.InstalledFiles
        if cached:
            installed_files = set()
            for node_id, package in cached:
                node = glb.pnodes.GetNode(node_id)
                setattr(node.attributes, 'package', package)
                installed_files.add(node)
            self.__installed_files = installed_files
        else:
            try:
                del self.__installed_files
            except AttributeError:
                pass

    def hasPartFileChanged(self):
        '''Has the Part File defining this section changed in some way

        This can include if the Parent Parts file changed, as this could change
        what the children Part files would define.
        '''
        return glb.pnodes.GetPNode(self.Stored.PartID).hasFileChanged()

    def TagDirectDependAsLoad(self, load_manager):
        try:
            return self._cache['TagDirectDependAsLoad']
        except KeyError:
            # get stored data
            stored_data = self.Stored

            if stored_data is None:
                self._cache['TagDirectDependAsLoad'] = False
                # return False to signal there was a cache issue
                return False
            # set our state
            self.ReadState = glb.load_file

            for dep in stored_data.DependsOn:
                sec = glb.pnodes.GetPNode(dep.SectionID)
                if not sec.TagDirectDependAsLoad(load_manager):
                    self._cache['TagDirectDependAsLoad'] = False
                    return False
            self._cache['TagDirectDependAsLoad'] = True
            # set our root parts
            pobj = glb.pnodes.GetPNode(stored_data.PartID)
            parent = pobj.Parent
            try:
                try:
                    tmp = glb.pnodes.GetPNode(parent.Stored.SectionIDs[self.Name])
                except KeyError:
                    tmp = glb.pnodes.GetPNode(parent.Stored.SectionIDs['build'])
                if not tmp.TagDirectDependAsLoad(load_manager):
                    self._cache['TagDirectDependAsLoad'] = False
                    return False
            except AttributeError:
                pass
            return self._cache['TagDirectDependAsLoad']

    @property
    def ReadState(self):
        if not self.Part:
            return glb.pnodes.GetPNode(self.Stored.PartID).ReadState
        return self.Part.ReadState

    @ReadState.setter
    def ReadState(self, state):
        if not self.Part:
            glb.pnodes.GetPNode(self.Stored.PartID).UpdateReadState(state)
        else:
            self.Part.UpdateReadState(state)

    @property
    def ID(self):
        try:
            return self._ID
        except AttributeError:
            self._ID = result = sys.intern("{1}::{0}".format(self.Part.ID, self.Name))
            return result


class build_section(section):
    __slots__ = []

    def __init__(self, pobj=None, ID=None):
        super(build_section, self).__init__(pobj, ID)

    @staticmethod
    def _process_arg(pobj=None, **kw):
        id = kw.get('ID')
        setup = False
        if pobj:
            id = "{1}::{0}".format(pobj.ID, 'build')
            setup = True
        elif id is None:
            raise ValueError("Invalid arguments values when creating section type")

        return id, setup

    @section.Name.getter
    def Name(self):
        return "build"


class utest_section(section):
    __slots__ = []

    def __init__(self, pobj=None, ID=None, env=None):
        super(utest_section, self).__init__(pobj, ID)

    @staticmethod
    def _process_arg(pobj=None, **kw):
        id = kw.get('ID')
        setup = False
        if pobj:
            id = "{1}::{0}".format(pobj.ID, 'utest')
            setup = True
        elif id is None:
            raise ValueError("Invalid arguments values when creating section type")

        return id, setup

    @section.Name.getter
    def Name(self):
        return "utest"


pnode_manager.manager.RegisterNodeType(build_section)
pnode_manager.manager.RegisterNodeType(utest_section)

# util functions


def scmp(x, y):
    xp = glb.pnodes.GetPNode(glb.pnodes.GetPNode(x.Stored.PartID).Stored.RootID)
    yp = glb.pnodes.GetPNode(glb.pnodes.GetPNode(y.Stored.PartID).Stored.RootID)
    return cmp(xp._order_value, yp._order_value)
