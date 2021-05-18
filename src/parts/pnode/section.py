

import _thread
import functools
import hashlib
import os
import pprint
import sys
import time
from builtins import filter
from typing import (Callable, Dict, List, Optional, Sequence, Set, Tuple,
                    Union, cast)

import parts.api as api
import parts.common as common
import parts.core.builders as builders
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
from parts.core.states import GroupLogic, LoadState
from parts.dependent_ref import dependent_ref
import parts.node_helpers as node_helpers
from SCons.Script import _SConscript as SConscript


class Section(pnode.PNode):
    """description of class"""
    __slots__ = [
        '_ID',  # generated.. this is the generate value
        # '__depends',  # what we depend on directly (ie explicitly), as list (order needed) of ComponentRef objects
        # '__full_depends',  # what depend on directly and indirectly

        '__classically_mapped',  # tells us if we have classically mapped Depends on data to deal with
        '__exports_dynamic_values',  # exports dynamic item that are not known until after the build does a scan
        '__exports',  # value we will export
        '__export_as_depends',  # list of values exported to map as a depends node, when they are referenced in a dependson call

        # '__build_context_files', # File that contain code for the builder (or best guess)
        # these are the node based on the section as a whole, works for new and classic formats
        '__target_nodes',  # target node for this section
        '__source_nodes',  # Source node for this section
        '__installed_files',  # anything that gets installed for packaging.
        # if we defining the "new" sections format these are the nodes
        # based on the phase they are defined with. This will have a combo of phase and phase-group
        '__group_target_nodes',  # target node for that are mapped to a given (phase,group) it was defined with
        '__group_source_nodes',  # Source node for that are mapped to a given (phase,group) it was defined with



        '__pobj',  # reference to the part containing this section.
        '__metasection',  # reference to the object that contain meta information.
        '__env',  # the environment for the given section (cloned from Parts object)
        '__user_env_diff',
        '__cache'  # any cached
    ]

    # define type of slot vars
    __exports_dynamic_values: bool

    def __init__(self, pobj, proxy):  # , ID=None):

        # if ID:
        #self._ID = ID

        # if pobj:
        self.__pobj = pobj
        self.__metasection = proxy._metasection

        self.__classically_mapped = False

        super().__init__()

    def _setup_(self, env=None, *lst, **kw):
        '''
        Setup and bind an environment to this section.
        '''
        if env:
            self.__env = env.Clone(**kw)
        else:
            self.__env = self.__pobj.Env.Clone(**kw)
        self.__env['PART_SECTION'] = self.Name

    @property
    def _metasection(self):
        return self.__metasection

    @ property
    def ID(self):
        try:
            return self._ID
        except AttributeError:
            self._ID = result = sys.intern("{1}::{0}".format(self.Part.ID, self.Name))
            return result

    @ property
    def Name(self):
        '''
        Get the name of the section
        This is defined by the metasection objects
        '''
        #raise NotImplementedError
        return self.__metasection.Name

    @ property
    def Exports(self):  # mutable
        '''
        Get currently defined export items from this section
        '''
        try:
            return self.__exports
        except AttributeError:
            self.__exports = result = dict()
            return result

    @ property
    def ExportAsDepends(self):
        try:
            return self.__export_as_depends
        except AttributeError:
            self.__export_as_depends = result = list()
            return result

    @property
    def hasDynamicExports(self) -> bool:
        '''
        Tells us that we have value that are exported based on some dynamic builder
        being called in this sections or via a dependent that this section would have
        added to the export table.

        This function can only be called after the section is processed to be 100% correct
        '''
        try:
            return self.__exports_dynamic_values
        except AttributeError:
            # given this is not set by a builder/scanner that is doing dynamic logic
            # we want to verify that a dependent does not export some value that would
            # effect our export table
            self.__exports_dynamic_values = False
            for depend in self.Depends:
                if depend.Section.hasDynamicExports and not self.__exports_dynamic_values:
                    for req in depend.Requires:
                        # check the dependent requirements are not internal
                        # and we are not forcing the internal value to the default
                        # we make sure items that are not internal and forced
                        # don't map with "dynamic" value generatation
                        if not req.is_internal and not req.is_internal_forced:
                            self.__exports_dynamic_values = True
                            break
            return self.__exports_dynamic_values

    @hasDynamicExports.setter
    def hasDynamicExports(self, value: bool):
        self.__exports_dynamic_values = value

    @ property
    def GroupedTargets(self):
        try:
            return self.__group_target_nodes
        except AttributeError:
            self.__group_target_nodes = result = {}
            return result

    @ property
    def GroupedSources(self):
        try:
            return self.__group_source_nodes
        except AttributeError:
            self.__group_source_nodes = result = {}
            return result

    @ property
    def Targets(self):
        '''
        All known targets for this section
        '''
        try:
            return self.__target_nodes
        except AttributeError:
            self.__target_nodes = result = set()
            return result

    @ property
    def Sources(self):
        try:
            return self.__source_nodes
        except AttributeError:
            self.__source_nodes = result = set()
            return result

    @ property
    def InstalledFiles(self):
        try:
            return self.__installed_files
        except AttributeError:
            self.__installed_files = result = set()
            return result

    @ property
    def Depends(self) -> List[dependent_ref]:
        '''
        This delagates to ??? to handle hold the depends list
        '''
        return self.__metasection.Depends

    @ Depends.setter
    def Depends(self, val: dependent_ref) -> None:
        '''
        This delagates to ??? to handle hold the depends list
        '''
        self.__metasection.Depends = val

    def DependentSections(self):
        '''
        Resolve the section we directly depend on.
        Items are cached to avoid extra work.
        '''

        if not self._cache.get('dependent_sections'):
            tmp = []
            for dependent in self.Depends:
                if dependent.hasMatch and not dependent.hasAmbiguousMatch:
                    tmp.append(dependent.Section)
                elif dependent.hasAmbiguousMatch:
                    msg = dependent.AmbiguousMatchStr()
                    api.output.error_msg(f"Mapping dependent for {self.ID}\n {msg}", stackframe=dependent.StackFrame)
                elif dependent.isOptional:
                    api.output.warning_msg(
                        f"Optional dependency {dependent.PartRef.Target} not found for {self.ID}", stackframe=dependent.StackFrame)
                else:
                    msg = dependent.NoMatchStr()
                    api.output.error_msg(
                        f"Dependency {dependent.PartRef.Target} not found for {self.ID}\n {msg}", stackframe=dependent.StackFrame)

            self._cache['dependent_sections'] = tmp
        return self._cache['dependent_sections']

    def DependsSorted(self):
        '''
        Sorts the depends the best we can to respect user order, but make sure depends ordering of the dependents
        are enforced to allow toolschains to work correctly.
        Order is node that should be more to the bottom are first
        '''

        try:
            return self._cache['sorted_depends']
        except KeyError:
            # Since we tend to have other information.. we use that to get sorted depends
            full_depends = self.FullDependsSorted
            depends = [depend for depend in self.Depends if depend.hasMatch]

            def cmp(x, y):
                if x in y.Section.FullDependsSorted:
                    return 1
                elif y in x.Section.FullDependsSorted:
                    return -1
                return self.Depends.index(x)-self.Depends.index(y)
            depends.sort(key=functools.cmp_to_key(cmp), reverse=True)
            self._cache['sorted_depends'] = tuple(depends)
            return self._cache['sorted_depends']

    def ResolveDepends(self, env=None):
        '''
        Resolve the dependents in the Environment for the sections.
        '''

        # items we care about are:
        # * if any depends export items that are being dynamically generated
        # * do we have classic depends on mappings that can be filled in
        # * order of items need to be topologically sorted,
        #    * need to respect user order when the sort shows we have no direct depends

        # get depends sorted .. This should address sorting issues and respecting the
        # user defined order
        depends: Tuple[dependent_ref] = self.DependsSorted()
        api.output.verbose_msg('dependson', f"Mapping depends {depends}")
        if not env:
            env = self.Env
        for depend in depends:
            # for each depends we want to map item from the export table to this
            # components. Given modern mapping. Nothing is defined in the environment
            # from the dependents. This allows us to prepend unique all items correctly

            requirements = depend.Requires
            for req in requirements:

                map_val = map_requirement(env, req, depend)

                # check to see if this not an internal depends.
                # if it is not we need to add it to our export table
                if req.is_internal == False:
                    if map_val is None:
                        continue

                    api.output.verbose_msg('dependson', "  exporting", req.key, map_val)
                    if req.key not in self.Exports and req.is_list:
                        self.Exports[req.key] = [[]]

                    if req.is_list:
                        self.Exports[req.key] = common.extend_unique(self.Exports[req.key], [[map_val]])
                    else:
                        self.Exports[req.key] = map_val
                    if util.isList(self.Exports[req.key]) and util.isList(self.Exports[req.key][0]):
                        for sublst in self.Exports[req.key]:
                            if util.isList(sublst):
                                sublst[:] = common.extend_unique([], env.Flatten(sublst))
                    api.output.verbose_msg('dependson', "  Exported values", self.Exports[req.key])

    def ProcessSection(self):

        # map the depends
        self.ResolveDepends()

        # make sure we have bound the meta section do it can refer to the main sections as needed
        self.__metasection._bind_(self)

        # change cwd to the of the part file
        fs = self.Env.fs
        oldwd = fs.getcwd()
        buildDir = self.Env.Dir("$BUILD_DIR")
        buildDir._create()

        # variant dir for file out of parts tree but under SConstruct
        fs.VariantDir(self.Env.Dir('$OUTOFTREE_BUILD_DIR'), "#", self.Env['duplicate_build'])
        # variant dir for file out of SConstruct tree but under the root
        # this does not cover windows drives that are different from the current drive c:\
        fs.VariantDir(self.Env.Dir('$ROOT_BUILD_DIR'), "/", self.Env['duplicate_build'])

        try:
            fs.chdir(buildDir, change_os_dir=True)
        except:
            fs.chdir(buildDir, change_os_dir=False)
        SCons.Script.sconscript_reading += 1
        oldCallStack = SConscript.call_stack

        # call the meta section processing logic
        try:
            api.output.verbose_msg([f"loading.{self.ID}", 'loading'], f"Processing Section: {self.ID}")
            self.__metasection.ProcessSection(0)
        finally:
            api.output.verbose_msg([f"loading.{self.ID}", 'loading'], f"Processing Section: {self.ID} Done!")
            SCons.Script.sconscript_reading -= 1
            #sys.path = oldSysPath
            fs.chdir(oldwd, change_os_dir=True)
            SConscript.call_stack = oldCallStack

        # bind top level targets to the main Alias for building this section
        if self._metasection.definition.TargetMappingLogic == GroupLogic.GROUPED:
            # map the items based groups we have defined
            for group in self.Groups:
                [self._map_target(t, group) for t in self.TopLevelTargets(group=group)]

        elif self._metasection.definition.TargetMappingLogic == GroupLogic.TOP:
            # default map all top level items independent of groups
            [self._map_target(t) for t in self.TopLevelTargets()]
        # define the import builder for all items that will be imported
        import_out = builders.imports.map_imports(self.Env, self)
        dyn_import_out = builders.dyn_imports.map_dyn_imports(self.Env, self)
        # map targets with a depends on the imports, so they are mapped
        # in the environment before the target tries to build
        # ideally I would like to avoid this, but this allows everything to move forward
        # improvement that we can make on this are:
        # 1) have a sec.bottom_level_targets to reduce the set we add to (added now)
        # 2) have a way to force resolution of a node being build/up-to-date given
        #    There are nodes that are dynamically resolved in the task-master logic
        # Ideally this is only needed because dynamic builders add unknowns
        # that are not seen by normal scanners
        if import_out:
            #print(f"{import_out} -> {node_helpers.has_changed(import_out[0])} {dyn_import_out}")
            for target in self.BottomLevelTargets():
                api.output.verbose_msg([f"loading.{self.ID}", "loading"], f"Mapping {target.ID} <- {import_out.name}")
                self.Env.Depends(target, import_out)

        # for each section we also want to define a export file
        # that defines everything we will export from the component
        # to any component that might depend on it

        # this need to be dependent on the import file
        dyn_exports = []
        if self.hasDynamicExports:
            dyn_exports = self.Env._map_dyn_export_(dyn_import_out)
            api.output.verbose_msg([f"loading.{self.ID}", "loading"], f"Mapping {dyn_exports} <- {dyn_import_out}")

        export_jsn = self.Env._map_export_(import_out+dyn_exports)
        api.output.verbose_msg([f"loading.{self.ID}", "loading"], f"Mapping {export_jsn} <- {import_out+dyn_exports}")

        # define the top level aliases mappings
        # self._map_target(export_jsn) # map the export file to the top level alias
        # define node for the packages to bind to if needed
        self.Env.DynamicPackageNodes(export_jsn)
        self._map_targets()
        # because we exist. The REQ.EXISTS maps this value to any dependent Sections
        # because if this we need a node. We use the Alias node for the section.
        # as a reminder the Alias for a node is in the from of <section type>::alias::<part ID>
        # so values as build::alias::foo or unit_test::alias::foo, etc..
        self.Exports["EXISTS"] = self.Alias

    @ property
    def AlwaysBuild(self):
        return self._cache.get("always_build", False)

    @ AlwaysBuild.setter
    def AlwaysBuild(self, val):
        self._cache["always_build"] = val

    @ property
    def FullDepends(self) -> Set[dependent_ref]:
        '''
        Resolved the full depends of the section, ie explicit and implicit
        returns a list sorted of bottom most depends first
        '''
        try:
            return self._cache["full_depends_set"]
        except KeyError:
            # get the direct depends
            sections = self.DependentSections()
            if sections:
                # fill out all sub dependents
                self._cache["full_depends_set"] = get_dependent_sections(sections)
            else:
                self._cache["full_depends_set"] = []
            return self._cache["full_depends_set"]

    @ property
    def FullDependsSorted(self):
        '''
        Get the sorted tuple of depends.
        Bottom depends are first, with top level depends are last
        '''
        try:
            return self._cache["full_depends_sorted"]
        except KeyError:
            tmp = toposort(self.FullDepends)
            self._cache["full_depends_sorted"] = tuple(tmp) if tmp else tuple()
            return self._cache["full_depends_sorted"]

    @property
    def DefiningPhase(self):
        return self._cache.get("defining_section")

    @DefiningPhase.setter
    def DefiningPhase(self, val):
        if val is None:
            del self._cache["defining_section"]
        else:
            self._cache["defining_section"] = val

    @ property
    def Part(self):
        try:
            return self.__pobj
        except AttributeError:
            return None

    @ property
    def Env(self):
        try:
            return self.__env
        except AttributeError:
            self.__env = result = self.Part.Env.Clone()
            return result

    @ property
    def UserEnvDiff(self):
        '''
        Items that we set withing the section
        Might want to look at using Override environment to do this.
        '''
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

    @ property
    def Alias(self):
        try:
            self._cache["alias"]
        except KeyError:
            alias_str = '{0}::alias::{1}'.format(self.Name, self.__pobj.Alias)
            self._cache["alias"] = self.__env.Alias(alias_str)
        return self._cache["alias"]

    @property
    def Groups(self):
        '''
        defines all known groups that we might have a node mapped to
        '''
        if 'groups' not in self._cache:
            self.sort_node_targets()
        return self._cache["groups"]

    @property
    def Phases(self):
        '''
        defines all known phases that we might have a node mapped to
        '''
        if 'phases' not in self._cache:
            self.sort_node_targets()
        return self._cache["phases"]

    @property
    def TargetsByPhase(self):
        '''
        defines all known phases that we might have a node mapped to
        '''
        if 'phase_nodes' not in self._cache:
            self.sort_node_targets()
        return self._cache["phase_nodes"]

    @property
    def TargetsByGroup(self):
        '''
        defines all known phases that we might have a node mapped to
        '''
        if 'group_nodes' not in self._cache:
            self.sort_node_targets()
        return self._cache["group_nodes"]

    @property
    def TargetsByPhaseGroup(self):
        '''
        defines all known phases that we might have a node mapped to
        '''
        if 'phase_group_nodes' not in self._cache:
            self.sort_node_targets()
        return self._cache["phase_group_nodes"]

    def sort_node_targets(self):
        groups = set()
        phases = set()
        phase_nodes = {}
        group_nodes = {}
        phase_group_nodes = {}
        for key, targets in self.GroupedTargets.items():
            if key[0]:
                phases.add(key[0])
                phase_nodes.setdefault(key[0], set()).update(targets)
            if key[1]:
                groups.add(key[1])
                group_nodes.setdefault(key[1], set()).update(targets)
            if key[0] and key[1]:
                phase_group_nodes.setdefault(key, set()).update(targets)

        self._cache["groups"] = groups
        self._cache["phases"] = phases
        self._cache["phase_nodes"] = phase_nodes
        self._cache["group_nodes"] = group_nodes
        self._cache["phase_group_nodes"] = phase_group_nodes

    def TopLevelTargets(self, phase: str = None, group: str = None):
        '''
        returns the top level targets.. ie the targets that are not children
        of the other targets
        '''

        test_targets = set()

        if phase and group:
            test_targets = self.filter_system_nodes(self.TargetsByPhaseGroup[(phase, group)])
        elif group:
            test_targets = self.filter_system_nodes(self.TargetsByGroup[group])
        elif phase:
            test_targets = self.filter_system_nodes(self.TargetsByPhase[phase])
        else:
            # make copy
            test_targets = self.filter_system_nodes(self.Targets)
        targets = set(test_targets)

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

    def BottomLevelTargets(self):
        # for each target
        ret = []
        test_targets = {node for node in self.filter_system_nodes(self.Targets) if not node.ID.startswith(".parts.cache")}
        targets = set(test_targets)

        # stuff we know to skip
        skip_set = set()
        while targets:
            trg = targets.pop()
            for test_target in test_targets:
                if trg.is_child(test_target):
                    # test_target is under the trg
                    # trg cannot be bottom level target
                    skip_set.add(trg)
                    # we know that trg is to be skipped
                    # continue to next node
                    # continue
                elif test_target.is_child(trg):
                    # trg is under the test_target
                    # test_target cannot be bottom level target
                    skip_set.add(test_target)
                    # go ahead and remove it if we
                    targets.discard(test_target)

        ret = test_targets - skip_set
        api.output.verbose_msgf(
            ['bottom-level-mapping'],
            "Mapping nodes to '{}':\n{}", self.ID, common.DelayVariable(lambda: [n.ID for n in ret]))
        return ret

    def _map_target(self, node: Union[SCons.Node.Node, Sequence[SCons.Node.Node]], subtarget: Optional[str] = None) -> None:

        # if we have a sub-target, we will want to map it to the top-level target
        if subtarget:
            alias_str = f'{self._metasection.concepts[0]}::alias::{self.__pobj.Alias}::{subtarget}'
            node = self.__env.Alias(alias_str, node)

        alias_str = f'{self._metasection.concepts[0]}::alias::{self.__pobj.Alias}'
        self.__env.Alias(alias_str, node)

    def _map_targets(self):
        '''
        Here we map all known target files that happen in this component
        to the alias value, to ensure that it is built in case there are actions
        that are no mapped correctly to some action that is mapped to the alias
        such as and sdk or install action
        '''

        # This is the base Alias for a given Part
        alias = self.__pobj.Alias
        prime_concept = self._metasection.concepts[0]
        alias_str = f'{prime_concept}::alias::{alias}'
        alias_str_r = f'{alias_str}::'

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
            # loop to make sure we map this alias to root alias:
            child_alias = a1
            parent_part = self.Part
            while not parent_part.isRoot:
                parent_part = parent_part.Parent
                child_alias = self.__env.Alias(
                    f'{prime_concept}${{ALIAS_SEPARATOR}}${{PART_ALIAS_CONCEPT}}{parent_part.Alias}::', child_alias)
            tca = self.__env.Alias(f"{prime_concept}${{ALIAS_SEPARATOR}}", child_alias)

        else:
            # build::alias::foo -> build::alias::foo:: -> build::
            tca = self.__env.Alias(f"{prime_concept}${{ALIAS_SEPARATOR}}", a1)

        # map all the other concepts
        for concept in self._metasection.concepts[1:]:
            ca = self.__env.Alias(f'{concept}::alias::{alias}', a)
            self.__env.Alias(f'{concept}::alias::{alias}::', ca)
            if self.Part.isRoot:
                self.__env.Alias(f"{concept}${{ALIAS_SEPARATOR}}", tca)

        # might not be needed anymore...
        # add call back for latter full mapping of build context
        functors.map_build_context(self.Part)()

    def ESigs(self):
        '''
        Export Signitures as a dictionary of keys with csig
        The dictionary all us to see what change (esigs)
        While esig is a quick check to see that there is a change

        '''

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
        '''
        The content signature of all exported items
        '''

        try:
            return self._cache['esig']
        except KeyError:
            self.ESigs()
        return self._cache['esig']

    ##################################################
    # cache based APIs

    @ property
    def _cache(self):
        try:
            return self.__cache
        except AttributeError:
            self.__cache = result = dict()
            return result

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

    @ property
    def ReadState(self):
        if not self.Part:
            return glb.pnodes.GetPNode(self.Stored.PartID).ReadState
        return self.Part.ReadState

    @ ReadState.setter
    def ReadState(self, state):
        if not self.Part:
            glb.pnodes.GetPNode(self.Stored.PartID).UpdateReadState(state)
        else:
            self.Part.UpdateReadState(state)

    def LoadStoredInfo(self):
        tmp = glb.pnodes.GetStoredPNodeInfo(self)
        if tmp.PartID:  # quick sanity check that this is good data
            return tmp
        return None

    # def LoadFromCache(self):
    #     info = self.Stored
    #     # get out owning part
    #     self.__pobj = info.Part
    #     self.__env = self.__pobj.Env.Clone()
    #     self.__env['PART_SECTION'] = self.Name
    #     user_env_diff = info.UserEnvDiff
    #     if user_env_diff:
    #         self.__user_env_diff = dict(user_env_diff)
    #         self.__env.Replace(**self.UserEnvDiff)
    #     # import the values we export
    #     # We assume these are fully resolved so we don't need to get any data from anything this
    #     # section would have depended on
    #     exports = info.Exports
    #     if exports:
    #         self.__exports = dict(exports)

    #     # need to map these items as Aliases
    #     export_as_depends = info.ExportedRequirements
    #     if export_as_depends:
    #         self.__export_as_depends = list(export_as_depends)
    #         for export in export_as_depends:
    #             try:
    #                 self.__env.Alias("{0}::alias::{1}::{2}".format(self.Name, self.__pobj.Alias, export),
    #                                  self.Exports[export])
    #             except KeyError:
    #                 api.output.verbose_msgf(['cache_load_warning'],
    #                                         "{0} was not found in the exports dictionary. Mapping value of []", export)
    #                 self.__env.Alias("{0}::alias::{1}::{2}".format(self.Name, self.__pobj.Alias, export), [])
    #     cached = info.InstalledFiles
    #     if cached:
    #         installed_files = set()
    #         for node_id, package in cached:
    #             node = glb.pnodes.GetNode(node_id)
    #             setattr(node.attributes, 'package', package)
    #             installed_files.add(node)
    #         self.__installed_files = installed_files
    #     else:
    #         try:
    #             del self.__installed_files
    #         except AttributeError:
    #             pass

    # def hasPartFileChanged(self):
    #     '''Has the Part File defining this section changed in some way

    #     This can include if the Parent Parts file changed, as this could change
    #     what the children Part files would define.
    #     '''
    #     return glb.pnodes.GetPNode(self.Stored.PartID).hasFileChanged()

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
            self.ReadState = LoadState.FILE

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


def been_seen(depends: List[dependent_ref], seen):
    '''
    Returns True if all items have been seen, or if the depend list is empty
    '''

    for item in depends:
        if item.hasMatch and item.Section not in seen:
            return False
    return True


def dep_resolve(node, seen, stack_info):
    for depend in node.Depends:
        depend_sec = depend.Section

        stack_info.append(depend.StackFrame)
        if depend_sec in seen[1:]:
            api.output.error_msg(
                f"Circular dependency found when processing: Part: {seen[0].Part.Name} Section: {seen[0].ID}\n Stack frames:", stackframe=stack_info[0], exit=False)
            for d, s in zip(seen[1:], stack_info[1:]):
                api.output.error_msg(f" -> Part: {d.Part.Name} Section: {d.ID}", stackframe=s, exit=False, show_prefix=False)
            api.output.error_msg(f"Please inspect DependsOn calls in stack and break cycle at correct place.", show_stack=False)
        seen.append(depend_sec)
        dep_resolve(depend_sec, seen, stack_info)


def CircularDependencyError(data):
    seen = []
    for node in data:
        seen = [node]
        stack_info = []
        dep_resolve(node, seen, stack_info)


def toposort(data: Set[Section]) -> List[Section]:
    """
    Given a set of complete sections objects, this will sort the section into a list
    starting with least dependent item to most dependent.
    It expects a complete list of sections, nothing should be missing
    """
    ret: List[Section] = []
    # Special case empty input.
    if len(data) == 0:
        return ret

    seen: Set[Section] = set()

    while True:
        # Get a set of item that have all dependencies seen and or are empty
        ordered = set(item for item in data if been_seen(item.Depends, seen))
        seen.update([i for i in ordered])  # add these item to seen

        # if this is empty we should be done
        if not ordered:
            break
        ret.extend([o for o in ordered])
        # remove seen sections and store them in data
        data = {item for item in data if item not in seen}

    if len(data) != 0:
        CircularDependencyError(data)

    return ret


def get_dependent_sections(top_sections):
    '''
    return a set of all the sections needed to build the provided sections
    '''

    stack = list(top_sections)
    stack_size = len(top_sections)
    indx = 0

    while indx < stack_size:
        sobj = stack[indx]
        # get the depends for current section
        depends = sobj.DependentSections()
        for d in depends:
            if d not in stack:
                # add to known items
                stack.append(d)
                stack_size += 1
        indx += 1

    return set(stack)


def map_requirement(env, req, dependref):
    '''
    General requirement mapping function given the new sections
    '''

    # get the namespace for storing items locally
    try:
        tmpspace = env["DEPENDS"]
    except KeyError:
        tmpspace = common.namespace()
        env["DEPENDS"] = tmpspace

    namespaces = dependref.PartRef.Target.Name.split('.')
    for subspace in namespaces:
        try:
            tmpspace = tmpspace[subspace]
        except KeyError:
            tmpspace[subspace] = common.namespace()
            tmpspace = tmpspace[subspace]

    # check to see if what we should try to map
    # if the dependent item has dynamic exports we need use
    # the classic mappers else we map directly
    find_val = ''
    if dependref.isClassicallyMapped and dependref.Section.hasDynamicExports:
        # was mapped with the mapper logic and the dependent has exports that
        # are dynamically generated.. This mean everything is real done with the mapping
        # the given case. So just return
        return
    elif dependref.isClassicallyMapped:
        # this case if for item being mapped via the mapper logic, but we know that since the
        # component did not register any dynamically generated exports being created, we can
        # replace the mapper logic with the resolved values as we know what that value is at
        # this point in time.
        #print(dependref.Section.ID, "classic mapped!!!")
        find_val = req.value_mapper(dependref.PartRef.Target, dependref.SectionName, dependref.isOptional)
        if req.key in ("CPPDEFINES"):
            # this is special cases in SCons
            find_val = (find_val,)
    if dependref.Section.hasDynamicExports:
        # need to map in the classic mapper way as we just don't know
        map_val = req.value_mapper(dependref.PartRef.Target, dependref.SectionName, dependref.isOptional)
    elif dependref.isOptional and not dependref.hasMatch:
        # this is optional and it does not exist.
        if find_val:
            # replace items with
            del tmpspace[req.key]
            if req.is_public and req.is_list:
                env[req.key].remove(find_val)
            else:
                del env[req.key]

        # exit as there is nothing more to do
        # return None as there is nothing to map to an export if that was needed
        1/0
        return
    else:
        # map the data in the export table
        map_val = dependref.Section.Exports.get(req.key)
        #print(f"map_val for {dependref.Section.ID} {req.key}:{dependref.Section.Exports.get(req.key)}")
        if not map_val and not dependref.Section.hasDynamicExports:
            # nothing to map and the section exports are static
            return req.value_mapper(dependref.PartRef.Target, dependref.SectionName, dependref.isOptional)
        # else:
            # We have unknown or non static items. Be safe and map via delay subst() call
            #map_val = req.value_mapper(dependref.PartRef.Target, dependref.SectionName, dependref.isOptional)

    # map to the namespaced area
    # if this was classically mapped we are just replacing the old values with the resolved values
    api.output.verbose_msg([f"dependson.{req.key}", 'dependson'], "  Mapping private namespace", req.key, map_val)
    if map_val:
        tmpspace[req.key] = map_val
    elif find_val:  # was classically mapped
        del tmpspace[req.key]

    # check to see if this should be mapped at the top level
    if req.is_public:
        # it should be mapped at the top of the environment
        # check to see if this is a list/iterable or a non iterable
        if req.is_list:
            if find_val:
                # remove classically mapped mapper value
                # it might not be found if the item was mapped in a different environment object
                # that was cloned by the user. This happens in the classic format case

                if find_val in env.get(req.key, []):
                    env[req.key].remove(find_val)
                elif find_val[0] in env.get(req.key, []):
                    env[req.key].remove(find_val[0])

            api.output.verbose_msg([f"dependson.{req.key}", 'dependson'], "  Global list", req.key, map_val)
            if map_val:
                env.PrependUnique(
                    delete_existing=False,
                    **{req.key: common.make_list(map_val)}
                )
        elif map_val:
            # this should replace the existing value
            api.output.verbose_msg([f"dependson.{req.key}", 'dependson'], "  Global value", req.key, map_val)
            env[req.key] = map_val

    return map_val


pnode_manager.manager.RegisterNodeType(Section)
