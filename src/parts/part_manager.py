
from typing import List
import copy
import hashlib
import os
import time

from parts.dependent_ref import dependent_ref

from parts.core.states import (LoadState, FileStyle)
import parts.api as api
import parts.common as common
import parts.config as config
import parts.core.util as util
import parts.datacache as datacache
import parts.errors as errors
import parts.events as events
import parts.glb as glb
import parts.loadlogic as loadlogic
import parts.node_helpers as node_helpers
import parts.platform_info as platform_info
import parts.pnode as pnode
import parts.scm as scm
import parts.version as version
import parts.reporter
import SCons.Job
import SCons.Script
from parts.target_type import target_type
from SCons.Debug import logInstanceCreation


class part_manager:

    def __init__(self):

        self.__defined_sections = set()  # type IDs of all section type in the run that have been defined by some Part.
        self.parts = {}  # a dictionary of all parts objects by there alias value
        self.__name_to_alias = {}  # a dictionary of a known Parts name and possible alias that match
        self.__alt_names = {}  # This is a name mapping. Allows for mapping a part name as something different
        self.__to_map_parts = []  # stuff that needs to be mapped, else it is wasted space
        # used to help prevent wasting time on cases of incomplete cache data
        self.__hasStored = SCons.Script.GetOption("parts_cache")
        self.__part_count: int = 0  # number of parts we have defined..
        self.__root_part_count: int = 0  # number of Major parts/components we have defined..
        self.__loader = None
        glb.engine.CacheDataEvent += self.Store
        self.__new_parts = set()

        self.MappingEvent = events.Event()

    @property
    def Loader(self):
        return self.__loader

    def map_targets_sections(self):
        '''
        given current target that are provided.. We map this to set of sections that should be processed.
        This can only be called after all the part files have been read in.
        returns a list of sections to process, and a set of targets we could not map
        '''
        ret_pnodes = set()
        node_return = []

        for t in SCons.Script.BUILD_TARGETS:
            if isinstance(t, SCons.Node.Node):
                api.output.verbose_msg(['target_section_mapping'], "Target is SCons node")
                node_return.append(t)
                continue

            # this is a string we need to understand how to map it
            # make a target object from string
            tobj = target_type(t)
            if tobj.isAmbiguous:
                # The item is unclear for some reason. We need to clarify it a little.
                # Most likely it is a partname or alias
                # ie `scons foo` was given.. we don't know if foo is alias::foo or name::foo or a file item

                # use target to deal with cases of properties and or groups in the target
                ta = target_type(f"alias::{t}")
                tn = target_type(f"name::{t}")

                # test to see if this is an alias
                # test the name and map and user define alt name
                if self.__name_to_alias.get(self.__alt_names.get(tn.Name, tn.Name)):
                    api.output.verbose_msgf(['target_section_mapping'], 'Target: "{0}" is a known name', t)
                    tobj = tn
                elif glb.pnodes.isKnownPNode(ta.Alias):
                    api.output.verbose_msgf(['target_section_mapping'], 'Target: "{0}" is a known alias', t)
                    # reset the target object
                    tobj = ta
                else:
                    # This has to be some other scons node thing
                    node_return.append(t)
            if tobj.isAmbiguous:
                print(f"{tobj.OriginalString} is ambiguous")
                node_return.append(tobj.OriginalString)
                continue
                #api.output.error_msg(f"Target {tobj.OriginalString} does not map to a known Part")

            # get the section(s) we need for this target
            api.output.verbose_msgf(['target_section_mapping'], 'Mapping target: "{0}"', t)

            # If this is an Alias we know it is an alias
            if tobj.Alias:
                # we have an alias/id mapping so this is very exact. There can only be a 1:1 mapping for this.
                # if the alias was define in a recursive way this will return more than on items.. ie all the
                # subparts that define the current Section object that defines the current concept for the target
                alias_lst=[tobj]

            elif tobj.Name:
                # we have a name.. this can map to 1 or more items that share the same name in case of a cross build
                # we need to map the name to the set of possible alias/IDs we have
                # get the possible aliases for the names we have.
                alias_lst = self.__name_to_alias.get(self.__alt_names.get(tobj.Name, tobj.Name))
                # there is a case that might make this an alias
                if alias_lst:
                    alias_lst = [tobj.MapToAliasTarget(alias) for alias in alias_lst]
                else:
                    tobj.Alias = tobj.Name
                    tobj.Name = None
                    alias_lst=[tobj]

            else:
                # this should be some generic target like all or build:: or <concept>::::group
                alias_lst=[tobj]
                #api.output.error_msgf('Target: "{0}" if not a name or alias', t)

            # process the target set to do the mapping
            api.output.verbose_msgf(['target_section_mapping'], 'Section to map: {0}', [str(i) for i in alias_lst])
            # map the alias targets
            for alias in alias_lst:
                sobjs = glb.pnodes.TargetToSections(alias)
                if sobjs:
                    ret_pnodes.update(sobjs)
                else:
                    api.output.warning_msg(f"{alias} did not map to a defined section")

        api.output.verbose_msgf(['target_section_mapping'],
                                'Return:\n Sections: {0}\n Scons node: {1}',
                                [i.ID for i in ret_pnodes],
                                node_return
                                )
        return ret_pnodes, node_return

    # todo  Given no caching is working, This is not used

    def map_targets_stored_pnodes(self):
        '''
        Turn the targets into a list of pnodes or Node ( given if can't be mapped to a Pnode) objects
        '''

        ret_pnode = []  # the new target list
        ret_nodes = []

        stored_data = datacache.GetCache("part_map")

        if stored_data is None:
            self.__hasStored = False
            api.output.verbose_msg(['target_mapping'], "part_map data cache did not load, Loading everything")
            return
        stored_name_to_alias = stored_data['name_to_alias']

        for t in SCons.Script.BUILD_TARGETS:
            ret = []
            name_matches = None
            if isinstance(t, SCons.Node.Node):
                api.output.verbose_msg(['target_mapping'], "Target is SCons node")
                tmp = []
                self.add_stored_node_info(t, tmp)
                ret += tmp
                ret_nodes.append((t, tmp))
                if not self.__hasStored:
                    api.output.verbose_msgf(['target_mapping'], 'No Stored info found for "{0}", Loading everything', t.ID)
                    return
            else:
                # This is a string to a target we need to figure out
                tobj = target_type(t)
                # first see if this is ambiguous
                # ie this is something like 'foo'
                # we don't know if this is a name::foo, alias::foo or a directory called foo, etc
                if tobj.isAmbiguous:
                    # we want to figure out based on stored information is this something we should know about
                    known_parts = stored_data['known_parts']
                    ta = target_type("alias::" + str(t))
                    tn = target_type("name::" + str(t))

                    # this might be a name
                    name_matches = stored_name_to_alias.get(tobj.Name)
                    if name_matches:
                        # we have some matches
                        api.output.verbose_msgf(['target_mapping'], 'Target: "{0}" is a known name', tn.Name)
                        tobj = tn
                    # see if this is an alias we have
                    elif glb.pnodes.isKnownPNode(ta.Alias):  # known_parts.keys():
                        # this looks like an alias we should know about
                        api.output.verbose_msgf(['target_mapping'], 'Target: "{0}" is a known alias', t)
                        tobj = ta
                    elif glb.pnodes.isKnownNodeStored(t):
                        node = glb.pnodes.GetNode(t)
                        tmp = []
                        self.add_stored_node_info(node, tmp)
                        ret += tmp
                        ret_nodes.append((node, tmp))
                        if not self.__hasStored:
                            api.output.verbose_msgf(['target_mapping'], 'Target: "{0}" missing stored data, Loading everything', t)
                            return
                        api.output.verbose_msgf(['target_mapping'], 'Target: "{0}" is a known SCons node', t)
                        continue
                    else:
                        # we don't know this.. assume we have to load everything
                        api.output.verbose_msg(['target_mapping'], 'Target: "{0}" is a not known, Loading everything')
                        return None

                # process the target node into Alias nodes
                if tobj.Concept:
                    concept = tobj.Concept
                else:
                    concept = 'build'
                    tobj.Concept = concept
                if tobj.hasAlias:
                    # add the concept::alias section
                    # we make an alias node as this works best for
                    # all cases with groups or recursion
                    # is this alias a direct mapping to a pnode
                    a_str = str(tobj)
                    if glb.pnodes.isKnownPNodeStored(a_str):

                        node = glb.pnodes.GetNode(a_str)
                        tmp = []
                        self.add_stored_node_info(node, tmp)
                        ret += tmp
                        if not self.__hasStored:
                            api.output.verbose_msgf(
                                ['target_mapping'], 'Target: "{0}" missing stored data, Loading everything', tobj)
                            return
                        api.output.verbose_msgf(['target_mapping'], 'Target: "{0}" is a Alias', tobj)

                    # if it a mapping to an scons nodes that we can map to a set of pnodes
                    elif glb.pnodes.isKnownNodeStored(a_str):
                        # this is known alias, but not a known pnode type so it means that this might some
                        # type of alias made by a section for example utest::foo that was created by the section
                        # utest::alias::foo.sub1.
                        node = glb.pnodes.GetNode(a_str)
                        self.add_stored_node_info(node, ret)
                        if not self.__hasStored:
                            api.output.verbose_msgf(
                                ['target_mapping'], 'No stored information found for "{0}", Loading everything', tobj)
                            return
                        api.output.verbose_msgf(['target_mapping'], 'Target: "{0}" is a Alias', tobj)
                    else:
                        # this is not known.. backout
                        api.output.verbose_msgf(
                            ['target_mapping'], 'No stored information found for "{0}", Loading everything', tobj)
                        return None
                elif tobj.Name:
                    api.output.verbose_msgf(['target_mapping'], 'Target: "{0}" is a name', tobj)
                    if name_matches is None:
                        name_matches = stored_name_to_alias.get(tobj.Name)

                    if not name_matches:
                        api.output.verbose_msgf(['target_mapping'], 'No matches found for name, Loading everything', tobj)
                        return None  # we don't have any known found values.. backout

                    pobjs_lst = [glb.pnodes.GetPNode(i) for i in name_matches]
                    # try to process known values
                    # keep in mind this assume classic formats
                    # and it will get stuff wrong..
                    # what it can get wrong is loading stuff we might not build
                    # and even possibility not loading stuff ( ie in more complex cases of sub-parts with lots of Customization )
                    # however common simple cases should be ok ( ie no sub-parts or no to minimum Customization form the default settings)
                    # ideally setup with only new formats will not have these issues, as we can read first, and get need info
                    name_matches = self.reduce_list_from_target_stored(tobj, set(pobjs_lst))

                    def _map_alias(_pobj, _tobj):
                        # the section does not match the concept we want to use the Alias form to get the "sections"
                        # as this does an extra check for some cases in which the Alias maps to nodes that require
                        # special logic to happen, such as AlwaysBuild()
                        tstr = "{0}::alias::{1}{2}".format(_tobj.Concept, _pobj.Alias, "::" if tobj.isRecursive else "")
                        node = glb.pnodes.GetNode(tstr)
                        if node:
                            self.add_stored_node_info(node, [])
                        else:
                            return True
                        if not self.__hasStored:
                            api.output.verbose_msgf(
                                ['target_mapping'], 'Target: "{0}" missing stored data, Loading everything', tstr)
                            return True
                        return False

                    def get_subpart_section(_pobj):
                        for subid in _pobj.Stored.SubPartIDs:
                            subpobj = glb.pnodes.GetPNode(subid)
                            if tobj.Section != tobj.Concept:
                                _map_alias(subpobj, tobj)
                            secid = subpobj.Stored.SectionIDs.get(tobj.Section)
                            if secid:
                                tmp = glb.pnodes.GetPNode(secid)
                                ret.append(tmp)
                            get_subpart_section(subpobj)

                    if not name_matches:
                        api.output.verbose_msgf(['target_mapping'], 'No matched found for "{0}", Loading everything', tobj)
                        return None

                    for pobj in name_matches:
                        # the target mapping logic will handle the case of groups mapping
                        # for loading a section a group still requires us to load a whole section
                        # get stored section
                        if tobj.isRecursive:
                            # try to load this section
                            if tobj.Section != tobj.Concept:
                                _map_alias(pobj, tobj)
                            secid = pobj.Stored.SectionIDs.get(tobj.Section)
                            if secid:
                                tmp = glb.pnodes.GetPNode(secid)
                                ret.append(tmp)
                            # if we are recursive, we need to add all section from any subpart we can find.
                            get_subpart_section(pobj)

                        else:
                            if tobj.Section != tobj.Concept:
                                _map_alias(pobj, tobj)

                            # try to load this section
                            tmp = pobj.Stored.SectionIDs.get(tobj.Section)
                            tmp = glb.pnodes.GetPNode(tmp)
                            # did we find a section.. if not error and exist
                            if tmp is None:
                                api.output.verbose_msg(['warning', 'target_mapping'],
                                                       'Part {0} does not define a {1} section'.format(
                                                           pobj.Stored.Name, tobj.Section))
                            else:
                                ret.append(tmp)

                else:
                    # add the concept:: alias as we define this
                    tmp = glb.engine.def_env.Alias(concept + "::")[0]
                    api.output.verbose_msgf(['target_mapping'], 'Target: "{0}" is a concept', tobj)
                    self.add_stored_node_info(tmp, ret)
                    if not self.__hasStored:
                        api.output.verbose_msgf(
                            ['target_mapping'], 'No stored information found for "{0}", Loading everything', tobj)
                        return
                if tobj.hasGroups:
                    ret_pnode.append((ret, tobj.Groups))
                else:
                    ret_pnode.append((ret, None))
        return (ret_pnode, ret_nodes)

    # todo  Given no caching is working, this is not used ( would be in some load logics)
    def LoadSection(self, sec):

        # when we load a section we in a way load the part that defines the section
        # there are a few different cases that can happen
        # 1) the section is ignored ( we don't care about it), but the Part needs to be loaded from file or cache
        # 2) the section is to load from cache, but the Part needs to be loaded from file
        # 3) the section and part have same load requirements
        # in general as we don't have "new formats" yet the section and parts are always 3)
        # the part can never be lower than the sections read state, the Parts is always
        # equal or higher
        pobj = glb.pnodes.GetPNode(sec.Stored.PartID)

        if sec._remove_cache:
            api.output.verbose_msgf(['loading'], "{0} being ignored as it seems to not exist in the SConstruct anymore", pobj.ID)

        if (sec.LoadState < LoadState.FILE and sec.ReadState == LoadState.FILE):
            self.LoadPart(pobj)
            if pobj._remove_cache:
                sec._remove_cache = True
            else:
                sec.LoadState = LoadState.FILE  # should be set.. just being safe
        elif (sec.LoadState < LoadState.CACHE and sec.ReadState == LoadState.CACHE):
            self.LoadPart(pobj)  # load part from cache (function will do nothing if already loaded)
            if pobj._remove_cache:
                sec._remove_cache = True
            elif sec.LoadState < LoadState.CACHE:
                sec.LoadFromCache()  # load section from cache
                sec.LoadState = LoadState.CACHE

    # this caching logic is not used.. but this is still a core function

    def LoadPart(self, pobj):
        part_file_load_time = time.time()
        processed = False
        # see if this part is setup
        if pobj._remove_cache:
            api.output.verbose_msgf(['loading'], "{0} being ignored as it seems to not exist in the SConstruct anymore", pobj.ID)
        elif pobj.isSetup:
            # read in the data fully
            if True:  # hacking at the moment for above if logic commented out
                api.output.verbose_msg(['loading'], f"Loading from file: {pobj.ID}")

                pobj.isLoading = True
                # set how we want to load this
                # item
                pobj.UpdateReadState(LoadState.FILE)
                # lead the files (and sub parts)
                pobj.ReadFile()

                # register any sections
                [self.__defined_sections.add(sec) for sec in pobj.Sections]

            #api.output.verbose_msg(['loading'],"{0:60}[{1:.2f} secs]".format(msg,(time.time()-part_file_load_time)))
            #api.output.console_msg(" Loading %3.2f%% %s \033[K"%((cnt/total*100),msg))
            # cnt+=1
                pobj.LoadState = LoadState.FILE
                processed = True
                pobj.isLoading = False

        if processed:
            api.output.verbose_msgf(['loading'], "Loaded {0:45}[{1:.2f} secs]", pobj.ID, (time.time() - part_file_load_time))

    # might want to re-think this function
    def _define_sub_part(self, env, alias, parts_file, mode=[], scm_type=None,
                         default=False, append={}, prepend={}, create_sdk=True, package_group=None,
                         **kw):

        parent_part = self._from_env(env)
        parent_part._cache['name_must_be_set'] = True
        # here we setup stuff we need to pass down from the parent
        new_kw = {}
        new_append = {}
        new_prepend = {}
        new_kw.update(parent_part._kw)
        new_append.update(parent_part._append)
        new_prepend.update(parent_part._prepend)

        if scm_type is None:
            scm_type = parent_part.Scm
            new_kw['CHECK_OUT_DIR'] = new_kw['SCM'] = parent_part.Env.subst("$CHECK_OUT_DIR")
        if package_group is None:
            package_group = parent_part.PackageGroup
        if mode == []:
            mode = parent_part.Mode
        new_kw.update(kw)
        if 'parent_part' in new_kw:
            del new_kw['parent_part']
        new_append.update(append)
        new_prepend.update(prepend)
        tmp = glb.pnodes.Create(pnode.part.Part, alias=alias, file=parts_file, mode=mode, scm_t=scm_type,
                                default=default, append=new_append, prepend=new_prepend,
                                create_sdk=create_sdk, package_group=package_group,
                                parent_part=parent_part, **new_kw)

        # make sure that if the parent is being loaded
        # that we load this from cache
        if parent_part.ReadState == LoadState.FILE and tmp.ReadState == LoadState.NONE:
            tmp.UpdateReadState(LoadState.CACHE)

        # setup new object
        # tmp._setup_()
        # add to set of known parts
        if tmp.isSetup:
            # see if this should be reading
            self._add_part(tmp)
            self.LoadPart(tmp)
        else:
            print(tmp.ID, "is NOT SETUP!!!!!!!!")

        # store setup state if this is a read cache or ignore case, as it might need to load latter as a file
        # and we will not be able to get the original state to "reinit" this component
        if tmp.ReadState != LoadState.FILE:
            tmp_args = new_kw
            tmp_args.update({
                            'alias': alias,
                            'file': parts_file,
                            'mode': mode,
                            'scm_t': scm_type,
                            'default': default,
                            'append': new_append,
                            'prepend': new_prepend,
                            'create_sdk': create_sdk,
                            'package_group': package_group,
                            'parent_part': parent_part
                            })
            tmp._cache["init_state"] = tmp_args

        if tmp.LoadState == LoadState.CACHE:
            # If this is the case we need to make sure the sections are processed
            for secid in tmp.Stored.SectionIDs.values():
                s = glb.pnodes.GetPNode(secid)
                if s.ReadState == LoadState.CACHE:
                    s.LoadFromCache()  # load section from cache
                    s.LoadState = LoadState.CACHE

        return tmp

    def map_scons_target_list(self) -> None:
        '''
        Here we try to map the Parts target values to alias nodes SCons can build
        '''

        stored_data = datacache.GetCache("part_map")
        # trying to translate based on everything being read in
        new_list = []  # the new target list
        skip_list = []

        def _add_list(_nodestr, original_str, target_obj):
            '''
            This is a helper functions to test if the node is known and or possibly valid
            before we try to add the node to the target list
            '''

            # if glb.pnodes.isKnownNodeStored(_nodestr):
            #    pass
            # elif not glb.pnodes.isKnownNode(_nodestr) and not target_obj.hasAlias:
            #    # This is not defined or known in the cache
            #    # since it is not defined or known to be a valid target we error
            #    api.output.error_msgf("{0} is an invalid target",original_str)#,show_stack=False)

            new_list.append(_nodestr)

        api.output.verbose_msgf(['loading'], "original BUILD_TARGETS: {0}", SCons.Script.BUILD_TARGETS)
        for t in SCons.Script.BUILD_TARGETS:
            tobj = target_type(t)
            # first see if this is ambiguous
            if tobj.isAmbiguous:
                # we are not sure
                # first we try to see if the name can be matched
                ta = target_type(f"alias::{t}")
                tn = target_type(f"name::{t}")
                if self.__name_to_alias.get(self.__alt_names.get(tn.Name, tn.Name)):
                    # we are sure this is a Parts value
                    tobj = tn
                # see if this is an alias value
                elif self.parts.get(ta.Alias):
                    # we are sure this is a Parts value
                    tobj = ta
                else:
                    # we are sure this is a SCons value
                    new_list.append(t)
                    continue

            # we are that this is a Part target format
            # see what concept is defined
            if tobj.Concept:
                concept = tobj.Concept
            else:
                concept = 'build'
            if tobj.Alias:
                # add the concept::alias alias as we define this
                basestr = f"{concept}::alias::{tobj.Alias}"
                if tobj.hasGroups:
                    for grp in tobj.Groups:
                        basestr = f"{basestr}::{grp}"
                        if tobj.isRecursive:
                            basestr = f"{basestr}::"
                        _add_list(basestr, t, tobj)
                else:
                    if tobj.isRecursive:
                        basestr = f"{basestr}::"
                    _add_list(basestr, t, tobj)

            elif tobj.Name:
                # This case can have multipul matches
                # get a list of known alias that have this name
                alias_lst = self.__name_to_alias.get(self.__alt_names.get(tobj.Name, tobj.Name))

                # this might be a case in which the target name is really an Alias
                # given alias_lst is none
                if alias_lst is None and tobj.Name in self.parts:
                    tobj.Alias = tobj.Name
                    tobj.Name = None
                    pobj_lst = [self.parts[tobj.Alias]]
                else:
                    pobj_lst = [self._from_alias(i) for i in alias_lst]
                # filter out any of these that don't match the properties
                pobj_lst = self.reduce_list_from_target(tobj, set(pobj_lst))
                if not pobj_lst:
                    api.output.error_msg(f'"{t}" did not map to any defined Parts')
                for pobj in pobj_lst:
                    basestr = f"{concept}::alias::{pobj.Alias}"
                    if tobj.hasGroups:
                        for grp in tobj.Groups:
                            basestr = f"{basestr}::{grp}"
                            if tobj.isRecursive:
                                basestr = f"{basestr}::"
                            _add_list(basestr, t, tobj)
                    else:
                        if tobj.isRecursive:
                            basestr = f"{basestr}::"
                        _add_list(basestr, t, tobj)
            else:
                # add the concept:: alias as we define this
                basestr = "{0}::".format(concept)
                if tobj.hasGroups:

                    # fix up later.. till then error if this case is used
                    api.output.error_msg('Target case of <concept>::::<group> is not supported yet!')
                    # we have groups so we need to get all the
                    # sections that mapped to this

                    # for each part with this section we test to see if it has this group
                    for pobj in self.parts.values():
                        if pobj.hasSection(tobj.Section):
                            pobj.Section(tobj.Section).groups
                    # if it does add it to the build list, else skip it

                    for grp in tobj.Groups:
                        basestr = "{0}::{1}".format(basestr, grp)
                        if tobj.isRecursive:
                            basestr = "{0}::".format(basestr)
                        _add_list(basestr, t)
                else:
                    _add_list(basestr, t, tobj)
        SCons.Script.BUILD_TARGETS = new_list
        if skip_list:
            api.output.verbose_msgf(['loading'], "Targets we skipped: {0}", skip_list)
        api.output.verbose_msgf(['loading'], "Updated BUILD_TARGETS: {0}", SCons.Script.BUILD_TARGETS)

    def ProcessParts(self) -> None:
        '''
        This function will process all the Parts object based on the targets
        '''

        #######################################################
        # update the disk
        # is everything up to date on disk update file on disk?
        # if not we need to update it
        if SCons.Script.GetOption('update'):
            api.output.print_msg("Updating disk")
            self.UpdateOnDisk(list(self.parts.values()))
            api.output.print_msg("Updating disk - Done")

        if len(SCons.Script.BUILD_TARGETS) == 1 and SCons.Script.BUILD_TARGETS[0] == "extract_sources":
            return

        targets = SCons.Script.BUILD_TARGETS
        # check to see that we even have targets to process
        if targets == []:
            return
        sections_to_process = []
        nodes = []

        #self.__loader = loadlogic.all.All(self)
        #up_to_date = self.__loader()

        # get all the root parts we have defined
        parts_to_load = list(self.parts.values())
        # sort them so they load in the order they are defined
        parts_to_load.sort(key=lambda x: x._order_value)

        total = len(parts_to_load) * 1.0
        cnt = 0
        # in case of a fallback we really want to make sure
        # all known parts are loaded from file. We need to set
        # that state, so any promotions forms of cache to file
        # happen correctly
        t1 = time.time()

        for pobj in parts_to_load:
            # have the part manager read the given part
            self.LoadPart(pobj)
            api.output.console_msg("Loading {0:.2%} \033[K".format(cnt / total))
            cnt += 1
        num_parts = len(self.parts)
        tt = time.time() - t1
        if num_parts:
            api.output.verbose_msgf(['loading', 'load_stats'],
                                    "Loaded {0} Parts\n Total time:{1} sec\n Average Time per part:{2}", num_parts, tt, tt / num_parts)
        api.output.print_msg("Loaded {0} Parts".format(num_parts,))

        # now that all the parts are loaded we want to start mapping sections based on
        # the targets. And only process the sections that should be in the depends chain.
        # classic parts will be fully loaded. so only post mapping for these items.
        # since we know all parts and sections at this time. We can map top level
        # targets that refer to a section/part. Only Node are to really known as they
        # might be defined in a sections we have to process.
        top_sections, unknown = self.map_targets_sections()

        if unknown:  # These are node targets or strings we don't know how to map
            # load all items? <expensive> and replace sobjs with this
            ##############
            # for the moment load everything.. will want to be a little smarter
            full_section_set = glb.pnodes.KnownSections()
            api.output.verbose_msgf(['loading', 'load_stats'],
                                    "Loading everything")
        else:
            # we need to sort the sobjs and add the depends.
            # this make a list in top item is first and anything below it needs to be loaded
            # as it might be a dependent item.
            full_section_set = pnode.section.get_dependent_sections(top_sections)
        # get sections.. order first items are on the bottom
        # top level sections are at the back
        order_sections = pnode.section.toposort(full_section_set)


        # loop the order sections first to last
        # we load each section. The section itself know how to load itself
        # when loading the logic give he whole list of items to load.
        # his allow a section type to do full
        import pprint
        glb.processing_sections=True
        num_sec=len(order_sections)
        start_total=time.time()
        for cnt, sobj in enumerate(order_sections):
            # Process each sections
            # Given no new sections are defined this is basically a noop call
            api.output.console_msg(f"Processing {cnt}/{num_sec} sections {(cnt/num_sec)*100.0:.2f}% Done.")
            st = time.time()
            sobj.ProcessSection()
            api.output.verbose_msg(['loading', 'load_stats'], f"Section {sobj.ID} took {time.time() - st:.04} seconds ")


        # after the section is processed we map various items
        # map the export data builder/or store data?
        # note... this allow dynamic builder to work as it
        # maps the dyn.json files used to delay other build items
        # that depend on the builder target to be built for getting new sources in a scanner call
        api.output.verbose_msg(["loading","load_stats"], f"Loaded {num_sec} sections in {time.time() - start_total}")
        api.output.print_msg(f"Total sections: {num_sec} Total known nodes: {glb.pnodes.TotalNodes}")
            # map target alias values
        glb.processing_sections=False

        # based on what is loaded map the targets
        # to Scons nodes that are used as build targets
        self.map_scons_target_list()
        # to do
        # load the "new" section logic

        # at this point everything is defined
        # clear node states ??  still needed?
        glb.pnodes.ClearNodeStates()


    def ProcessSection(self, sec_type, target):
        '''
        This function will fully process a section type for a given target
        '''
        # get function to handle processing
        func = sec_type.GetHandler()
        # call function with target to have defined for build
        func(self, target)

    def GetSectionsBasedOnTarget(self, target):
        '''
        This functions tries to map the alias to a given sections that would
        process the target correctly
        '''
        # parse the target to get any possible concepts
        if target.isPartTarget() == False:
            target.all = True
            if target.original_string not in ['all', '.']:
                api.output.warning_msg(
                    'Target "%s" is unknown to Parts, it may be known to SCons. Force reading all data' % target.original_string)
        if target.concept is None:  # no concept defined
            concept = 'build'
        else:
            concept = target.concept

        # get all sections that handle the given concepts
        ret = []
        for s in self.sections:
            if s.HandleConcept(concept):
                ret.append(s)
        return ret

    def UpdateOnDisk(self, part_set=None):
        ''' Update any parts that need to be updated on disk

        @param part_set The set of Part to see if they are up-to-date, if test all Parts
        '''
        # we need to see if any part needs to be checked out or updated
        # loop each part and ask it need to be updated

        # define the set of item to try to update
        if part_set is None:
            # nothing defined so check all known parts
            part_set = list(self.parts.values())

        # these are the list for item we will update on disk
        # we have a list of item we can do in parallel and item that
        # have to be done serial.
        p_mirror_list = scm.task_master.task_master() # items that can be mirrored
        p_list = scm.task_master.task_master() # items we can do in parallel
        s_list = scm.task_master.task_master() # items that have to be done serially

        # items we are updating on disk require update to the state files
        update_set = set([])

        self._get_scm_update_tasks(part_set, update_set, p_mirror_list, p_list, s_list)
        #########################################################
        # get value for level of number of concurrent checkouts
        scm_j = SCons.Script.GetOption('scm_jobs')
        if scm_j == 0:
            scm_j = SCons.Script.GetOption('num_jobs')

        ######################################
        # call the task logic with the SCons Job object to update item on disk
        try:
            if p_mirror_list._has_tasks():
                api.output.print_msg("Updating mirrors")
                self.do_disk_update(scm_j, p_mirror_list)
                api.output.print_msg("Updating mirrors - Done")
            if p_list._has_tasks():
                # get value for level of number of concurrent checkouts
                self.do_disk_update(scm_j, p_list)
            if s_list._has_tasks():
                self.do_disk_update(scm_j, s_list)
        finally:
            # we do this here to not have to run the tasks if there is
            # nothing to do
            for p in update_set:
                p.PostProcess()
            datacache.SaveCache(key='scm')

    def _get_scm_update_tasks(self, part_set, update_set, p_mirror_list, p_list, s_list):
        '''
        Break up the scm objects to parallel and serial list
        '''
        # update any extern part cases we need to update
        self._get_scm_extern_tasks(part_set, p_list, p_mirror_list, update_set)

        # this is the set of part we need to check for updating
        for p in part_set:
            # if so add to queue for checkout
            scmobj = p.Scm

            # can we mirror this?
            if scmobj.NeedsToUpdateMirror():
                p_mirror_list.append(scmobj, mirror=True)

            if scmobj.NeedsToUpdate():
                # we check to see if the scm object allow for the
                # parallel checkout policy.
                update_set.add(scmobj)
                if scmobj.AllowParallelAction():
                    p_list.append(scmobj)
                else:
                    s_list.append(scmobj)
            elif not scmobj.CacheFileExists:
                # update cache file if it does not exist
                update_set.add(scmobj)

    def _get_scm_extern_tasks(self, part_set, scm_objs, mirror_objs, update_set):
        '''

        '''
        # filter the part_set to get all item that have extern items
        part_set = [pobj for pobj in part_set if pobj.ExternScm]

        # for each item see if we have seen this item and if not add it to the
        # set of items to checkout. We detect if an item is seem by look at the
        # resolved $SCM_EXTERN_DIR value
        known_paths = []
        for pobj in part_set:
            path = pobj.ExternScm._env.subst("${SCM_EXTERN_DIR}")
            scm_obj = pobj.ExternScm
            if path not in known_paths:
                known_paths.append(path)
                if scm_obj.NeedsToUpdate():
                    update_set.add(scm_obj)
                    scm_objs.append(scm_obj)

                if scm_obj.NeedsToUpdateMirror():
                    mirror_objs.append(scm_obj, mirror=True)

    def do_disk_update(self, count: int, scm_objs: List[scm.base.base]):

        def post_scm_func(jobs, tm):
            if jobs.were_interrupted():
                tm.ReturnCode = 3
                api.output.error_msg("Updating of disk was interrupted!", show_stack=False)
            elif tm.Stopped:
                tm.ReturnCode = 4
                api.output.error_msg("Errors detected while updating disk!", show_stack=False)

        try:
            # create jobs objects
            jobs = SCons.Job.Jobs(count, scm_objs)
            # run the jobs
            jobs.run(postfunc=lambda: post_scm_func(jobs, scm_objs))
        except (parts.reporter.PartRuntimeError,) as e:
            if scm_objs.ReturnCode:
                glb.engine.def_env.Exit(scm_objs.ReturnCode)
            else:
                glb.engine.def_env.Exit(2)

    def MappingSig(self, name):

        md5 = hashlib.md5()
        for i in self.__name_to_alias[self.__alt_names.get(name, name)]:
            md5.update(i.encode())
        return md5.hexdigest()

    def StoredMappingSig(self, name):
        info = datacache.GetCache('part_map')
        return info.get('sig_mapping', {}).get(name, 'Invalid')

    def _add_part(self, object):
        if object.Alias is None:
            self.__to_map_parts.append(object)
            return
        self.__part_count += 1
        if object.Root._order_value == 0:
            if object.isRoot:
                self.__root_part_count += 1
                object._order_value = self.__root_part_count
            else:
                object._order_value = object.Root._order_value

        self.parts[object.Alias] = object
        glb.pnodes.AddPNodeToKnown(object)

    # don't think I need this
    '''def _clean_unknown(self, known_pobj):
        for i in self.__to_map_parts:
            if i.Name == known_pobj.Name and\
                i.Version == known_pobj.Version and\
                    i._kw.get('TARGET_PLATFORM', glb.engine.def_env['TARGET_PLATFORM']) == known_pobj.Env['TARGET_PLATFORM']:
                known_pobj._merge(i)
                self.__to_map_parts.remove(i)
                break'''

    def _from_alias(self, alias):
        '''
        given an alias get the defined part with this alias
        '''
        return self.parts.get(alias, None)

    def _from_env(self, env):
        '''
        given an env get the defined part with this alias
        '''
        if env is None:
            return None
        return self._from_alias(env.get('PART_ALIAS'))

    def section_from_env(self, env):
        if env:
            section_name = env.get("PART_SECTION")
            if section_name:
                pobj = self._from_env(env)
                return pobj.Section(section_name) if pobj else None
        return None

    def _has_name(self, name):
        ''' return True if we have reason to believe this is a Part name that is known
        We return True if We have a 100% match, in the known names. If this is empty
        we guess based on what in the cache
        '''
        if name in self._alias_list:
            return True
        # check the cache
        if _get_stored_root_alias(name) is not None:
            return True
        # we can't say that we know we have a Part with this name
        return False

    def _from_target(self, target, local_space=None, user_reduce=None, use_stored_info=False):
        '''
        Given a Target object we want to map this to the correct Part Object and section in that Part
        We might have a local mapping space define by the control what is mapped.
        This function returns all possible matches
        '''
        pobj_lst = []

        # user_reduce if not implemented ( may remove )
        # use_stored_info always fails at the moment ( until I fix the cache logic again)
        if use_stored_info:
            return []

        # if we have a local space defined by the user we want to look for possible matches in this space
        # ie this means if there is a possible match, there can be no match in the global space
        # if there is no possible match in the local space we will fallback to the global space for a match
        # by possible match. this is before we try to reduce the set the an exact value
        if local_space:
            for pobj in local_space:
                # Do we have an Alias define?
                if target.Alias == pobj.Alias:
                    # if so just return the Alias object if it is define
                    pobj_lst.append(pobj)
                    # we can only have one Alias match
                    break
                # do we have name that could match?
                elif target.Name == pobj.Name:
                    pobj_lst.append(pobj)

        # get the set of possible part objects that match based on the target name or alias (whichever is define)
        # did we have a local_space that we might have matched on? If not try the global space.
        if not pobj_lst:
            # Do we have an Alias define?
            if target.Alias:
                # if so just return the Alias object if it is define
                pobj_lst.append(self._from_alias(target.Alias))
            else:
                # this target is based on a name
                # based on the name get all possible Alias/IDs that could be a match
                for alias_str in self._alias_list(target.Name):
                    # turn the string to a pobj
                    pobj_lst.append(self._from_alias(alias_str))

        # we have items to match
        if pobj_lst:
            # reduce the set of possible parts for this target
            # to items that match the target
            ret = self.reduce_list_from_target(target, pobj_lst)
        else:
            # There is nothing to reduce
            ret = None

        return ret

    def reduce_list_from_target(self, tobj, part_lst):

        ret_lst = []
        api.output.trace_msgf("reduce_target_mapping", "Reducing list of parts based on target {0}", tobj)
        api.output.trace_msgf("reduce_target_mapping", "Full list of possible matches are {0}", [p.ID for p in part_lst])

        # we loop over all the "properties" and reduce based on values defined at that level
        for pobj in part_lst:
            match = True
            for key, val in tobj.Properties.items():
                api.output.trace_msgf("reduce_target_mapping", " Testing Part {0}", pobj.ID)
                if key == 'version':
                    # normalize string to version_range object
                    if util.isString(val):
                        val = version.version_range(val + '.*')
                    api.output.trace_msgf(
                        "reduce_target_mapping",
                        "  Matching Attribute: {key} Values: {val} with {tval}",
                        key=key,
                        val=val,
                        tval=pobj.Version
                    )
                    # do the test
                    if pobj.Version not in val:
                        match = False
                # check build config
                elif key in ['cfg', 'config', 'build-config', 'build_config']:

                    api.output.trace_msgf(
                        "reduce_target_mapping",
                        "  Matching Attribute: {key} Values: {val} Based on {tval}",
                        key=key,
                        val=val,
                        tval=pobj.Env["CONFIG"]
                    )

                    if pobj.ConfigMatch:  # TODO double check this line!
                        # test that the configuration is based on request value
                        # this allows "debug" to work when using my "MyCustonmDebug" config
                        if not pobj.Env.isConfigBasedOn(val):
                            match = False
                # check target_platform/platform_match
                elif key in ['platform_match', 'target', 'target-platform', 'target_platform']:
                    api.output.trace_msgf(
                        "reduce_target_mapping",
                        "  Matching Attribute: {key} Values: {val} with {tval}",
                        key=key,
                        val=val,
                        tval=pobj.PlatformMatch
                    )

                    if pobj.PlatformMatch != val:
                        part_lst.remove(pobj)
                elif key == 'mode':
                    val_list = val.split(',')
                    api.output.trace_msgf(
                        "reduce_target_mapping",
                        "  Matching Attribute: {key} Values: {val} with {tval}",
                        key=key,
                        val=val_list,
                        tval=pobj.Mode
                    )
                    # we might want to enhance this to say match on not having something
                    # or some reduce set. This currently only works well when the depend
                    # all test for a mode to exist. Empty set cases will most likely comeback
                    # as ambiguous.

                    # note. mode if not set by the root Part call, will add a "default" value
                    # to the mode. This can be used to help with the checking logic in certain case

                    # this is testing contains logic
                    for v in val_list:
                        if v not in pobj.Mode:
                            match = False
                            break

                else:
                    # look up in the parts environment
                    # This case is like the above "mode" case. Using it work best we there is no
                    # empty set, or the empty set was testing on something else to reduce ambiguous matches
                    try:
                        api.output.trace_msgf(
                            "reduce_target_mapping",
                            "  Matching Environment Variable: {key} Values: {val} with {tval}",
                            key=key,
                            val=val,
                            tval=pobj.Env[key]
                        )

                        if util.isList(pobj.Env[key]):
                            api.output.trace_msgf("reduce_target_mapping", "  Variable is a list in the Environment")
                            val_list = val.split(',')
                            api.output.trace_msgf("reduce_target_mapping",
                                                  "  Testing that Environment variable contains all values in {0}", val_list)
                            for v in val_list:
                                if v not in pobj.Env[key]:
                                    match = False
                                    break
                        else:
                            api.output.trace_msgf("reduce_target_mapping",
                                                  "  Variable is not a list in the environment Environment")
                            # if both cases are false then we have a failure
                            if pobj.Env[key] != val and str(pobj.Env[key]) != val:
                                api.output.trace_msgf("reduce_target_mapping", "   Removing Part {0}", pobj.ID)
                                match = False
                    except KeyError:
                        match = False
                if not match:
                    api.output.trace_msgf("reduce_target_mapping", "  Removing Part {0}", pobj.ID)
                    break

            if match:
                ret_lst.append(pobj)

        # do one last pass if we have more than one item. This allow for best version mapping.
        # This does need a better pass of thinking to have more best/strongest match, vs best version
        if len(ret_lst) > 1:
            api.output.trace_msgf("reduce_target_mapping", " Reducing based on best version {}", [p.ID for p in ret_lst])
            ret_lst.sort(key=lambda pobj: pobj.Version, reverse=True)
            ret_lst = [i for i in ret_lst if i.Version == ret_lst[0].Version]

        # return what was ever added as a Pobj
        api.output.trace_msgf("reduce_target_mapping", "Final reduced list {0}", [p.ID for p in ret_lst])
        return ret_lst

    def reduce_list_from_target_stored(self, tobj, part_lst):

        api.output.trace_msgf("stored_reduce_target_mapping",
                              "Reducing list of parts based on target {0}\n set={1}", tobj, part_lst)
        for k, v in tobj.Properties.items():
            for pobj in part_lst.copy():
                api.output.trace_msgf("stored_reduce_target_mapping", " Testing Part {0}", pobj.ID)
                if pobj.Stored is None:
                    # We have no stored info. skip test
                    # (ie load it as it might be needed)
                    pass
                elif k == 'version':
                    api.output.trace_msgf("stored_reduce_target_mapping",
                                          "  Matching Attribute: {0} Values:{1} {2}", k, v, pobj.Stored.Version)
                    if util.isString(v):
                        v = version.version_range(v + '.*')
                    if pobj.Stored.Version not in v:
                        api.output.trace_msgf("stored_reduce_target_mapping", "  Removing Part {0}", pobj.ID)
                        part_lst.remove(pobj)
                elif k in ['target', 'target-platform', 'target_platform']:
                    api.output.trace_msgf("stored_reduce_target_mapping",
                                          "  Matching Attribute: {0} Values:{1} {2}", k, v, pobj.Stored.TargetPlatform)
                    if pobj.Stored.TargetPlatform != v:
                        api.output.trace_msgf("stored_reduce_target_mapping", "  Removing Part {0}", pobj.ID)
                        part_lst.remove(pobj)
                elif k in ['platform_match']:
                    api.output.trace_msgf(
                        "stored_reduce_target_mapping",
                        "  Matching Attribute: {0} Values:{1} {2} Types:{3} {4}",
                        k,
                        v,
                        pobj.Stored.PlatformMatch,
                        type(v),
                        type(
                            pobj.Stored.PlatformMatch))
                    if pobj.Stored.PlatformMatch != v:
                        api.output.trace_msgf("stored_reduce_target_mapping", "  Removing Part {0}", pobj.ID)
                        part_lst.remove(pobj)
                elif k in ['cfg', 'config', 'build-config', 'build_config']:
                    # weak... make better code for this case
                    if pobj.Stored.ConfigMatch:
                        api.output.trace_msgf("stored_reduce_target_mapping", "  Matching Attribute: {0} Values:{1}", k, v)
                        if pobj.Stored.Config != v:  # pobj.Env.isConfigBasedOn(v):
                            api.output.trace_msgf("stored_reduce_target_mapping", "  Removing Part {0}", pobj.ID)
                            part_lst.remove(pobj)
                elif k == 'mode':
                    mv = v.split(',')
                    for v in mv:
                        if v not in pobj.Stored.Mode:
                            api.output.trace_msgf("stored_reduce_target_mapping", "  Removing Part {0}", pobj.ID)
                            part_lst.remove(pobj)
                            break
                else:
                    # look up in the parts environment
                    # skip this test for stored information
                    # as we don't have an env object yet
                    pass
        api.output.trace_msgf("stored_reduce_target_mapping", "Final reduced list {0}", part_lst)
        return part_lst

    def _alias_list(self, name=None):
        '''
        given an a part name return a list of all parts alias that
        could be matches for that name
        '''
        if name is None:
            return self.__name_to_alias
        return self.__name_to_alias.get(self.__alt_names.get(name, name), set([]))

    def add_name_alias(self, name, alias, oldname=None):
        try:
            self.__name_to_alias[name].add(alias)
        except KeyError:
            self.__name_to_alias[name] = set()
            self.__name_to_alias[name].add(alias)

        if oldname:
            try:
                # remove the alias from the set
                self.__name_to_alias[oldname].discard(alias)
                if not self.__name_to_alias[oldname]:
                    # delete the old name from the mapping table
                    del self.__name_to_alias[oldname]
            except KeyError:
                # old name does not exist
                pass

    def Store(self, goodexit, build_mode='build'):
        if goodexit:
            if isinstance(self.Loader, loadlogic.all.All):
                # clear out the cache
                datacache.StoreData("part_map", {})

            stored_data = datacache.GetCache("part_map")
            data = {'__version__': '1.0'}
            # we want to store information about the Parts we have in this run
            # or update any parts that are read in
            tmp = stored_data['known_parts'] if stored_data else {}
            has_old = False
            # this needed to tell if we have a alias target
            # however I may not need all the data that is stored here
            # we can clean this up later
            for k, v in self.parts.items():
                format = v.Format
                if format != 'new':
                    has_old = True
                # update only part that have been loaded from file
                if v.LoadState == LoadState.FILE:  # might need to relook at this case when we get new formats working
                    tmp[k] = {
                        'name': v.Name,
                        # 'version':v.Version,

                        'format': format,
                        'root_alias': v.Root.ID
                    }

            data["known_parts"] = tmp

            tmp = stored_data['name_to_alias'] if stored_data else {}
            sigmap = stored_data['sig_mapping'] if stored_data else {}
            # this is needed to help with name targets
            for name, partIDs in self.__name_to_alias.items():
                # make sure we merge in data correctly
                # get any stored info we have
                tmp2 = tmp.get(name, set([])) if self.__hasStored else set([])
                # add any new mappings we have
                for partID in partIDs:
                    tmp2.add(partID)
                tmp[name] = tmp2
                sigmap[name] = self.MappingSig(name)
            data['name_to_alias'] = tmp
            data['sig_mapping'] = sigmap
            # not sure about this one
            data["hasClassic"] = has_old

            datacache.StoreData("part_map", data)

    def add_stored_node_info(self, node, nlist):
        ''' this function tries to figure out if the given node depends on any parts
        If it does it add the information, if it does not it adds the node itself
        '''
        # check to see if the cache is good
        if self.__hasStored == False:
            return
        # get node data if any
        if node.Stored and node.Stored.Components:
            # we have parts information to add
            for partid, sectionids in node.Stored.Components.items():
                for section in sectionids:
                    section = glb.pnodes.GetPNode(section)
                    if node.Stored.AlwaysBuild:
                        section.AlwaysBuild = True
                    if section is None:
                        self.__hasStored = False
                    else:
                        nlist.append(section)
        elif node.Stored:
            # we are here because there as no data stored about what sections to
            # load for this node. This is not an issue as this node should have been
            # define by normal means.. we only need to see what it depends on

            # check the state to see if we seen this node
            if getattr(node, '_node_info_checked', False):
                return

            # check that we have binfo for this node
            if node.get_stored_info() is None:
                # this might be an Alias that was defined
                # we want to get any stored binfo we have and assign it
                if isinstance(node, SCons.Node.Alias.Alias):
                    binfo = glb.pnodes.GetAliasStoredInfo(node.ID)
                    if binfo:
                        # this is a little hacky... look at cleaning up..
                        class wrapper:

                            def __init__(self, binfo, ninfo=None):
                                if __debug__:
                                    logInstanceCreation(self)
                                self.binfo = binfo
                                self.ninfo = ninfo
                        node._memo['get_stored_info'] = wrapper(binfo)
                    else:
                        self.__hasStored = False
                        return
                else:
                    self.__hasStored = False
                    return

            # we have binfo
            binfo = node.get_stored_info().binfo
            nodes = getattr(binfo, 'bsources', []) + getattr(binfo, 'bdepends', []) + getattr(binfo, 'bimplicit', [])
            rlist = []
            # for each node we dependon see if we have stored info about what sections to load
            for n in nodes:
                # get each node we care about.
                tnode = glb.pnodes.GetNode(n)
                if tnode is None:
                    self.__hasStored = False
                    return
                tlist = []
                # check the children node
                self.add_stored_node_info(tnode, tlist)
                # set the node as being checked
                tnode._node_info_checked = True
                # add any node section to the list
                common.extend_unique(nlist, tlist)
        else:
            # there is no stored data.. cache bad or missing.
            self.__hasStored = False
        # set the node as being checked
        node._node_info_checked = True

    @property
    def NewRootParts(self):
        '''
        Returns a set of "new" Parts that are not known based on stored data from last run
        '''

        if self.__new_parts:
            return self.__new_parts

        stored_data = datacache.GetCache("part_map")
        if stored_data is None:
            self.__hasStored = False
            return None
        # get stored data on known Parts
        try:
            known_parts = stored_data['known_parts']
        except KeyError:
            self.__hasStored = False
            return None        # look to see if any parts we currently know about is not in the list.

        for pobj in self.parts.values():
            if pobj.ID not in known_parts:
                self.__new_parts.add(pobj)

        return self.__new_parts

    @property
    def ChangedParts(self):
        '''
        Returns a set of all Parts that have changed because the defining file is different
        '''
        ret = set()
        # we look up based on look at the stored information. If we don't have Stored information
        # we return all known Parts as this everything we know of.

        if self.__hasStored:
            # get the root parts that changed since the last run
            changedIDs = glb.pnodes.GetChangedRootPartIDsSinceLastRun()
            # for each root part we have did it inputs change
            for pobj in self.parts.values():
                if pobj.isRoot and (pobj.ID in changedIDs or self.hasInputChanged(pobj)):
                    ret.add(pobj)
                if self.__hasStored == False:
                    return None
        else:
            # get information based on what we loaded so far
            ret = None
        return ret

    def hasInputChanged(self, pobj):
        # currently we only check mode at the moment
        if pobj.Stored is None:
            api.output.verbose_msgf(["update_check"], "No stored data found for {0}, forcing load over everything", pobj.ID)
            self.__hasStored = False
            return False
        if pobj.Root.Mode != pobj.Stored.Root.Mode:
            api.output.verbose_msgf(["update_check"], "Input to the Part call for {0} has changed", pobj.ID)
            return True
        # need to fix the **KW
        # ie we want to pickle **kw in a part call, get a sig value for it, and know if all object are safe to
        # unpickle or do we need to load a defining file first to get the needed objects defined.
        return False

    @property
    def RootPartSig(self):
        '''
        Get a signiture of all root Parts files. This allows us to know if we can dynamically load the
        dependent Parts in the DependsOn() call or not.
        '''
        md5 = hashlib.md5()
        for pobj in self.RootPartSig:
            pobj.File.get_csig()
        return md5.hexdigest()

    def UpdateStoredState(self):
        '''
        This function finds all new and change parts file and loads them, and saves there state, so we have a clear
        picture what we need to process for building the targets.
        '''
        # Get New
        # first thing we need to do is make sure we add all Parts that are new
        # these have to be loaded even if we don't need them to build the target
        # this allows us to update the over all state of the build for the next pass
        # and allow us to simplify the load logic overall, making the common case
        # you tend to see as you develop code much faster

        parts_to_load = list(self.NewRootParts)
        # Get Changed
        # Now we want to get a set of all Parts that have file that files changed because the file is different
        # or because the content ( ie inputs) defining the file changed
        tmp = self.ChangedParts
        parts_to_load += tmp

        if not parts_to_load:
            return
        # at this point we have set all root Part we need to load from file state to fill in incomplete information
        # or any changed state information

        # sort the list
        parts_to_load.sort(pnode.part.pcmp)

        # load the Parts
        for pobj in parts_to_load:
            self.pmgr.LoadPart(pobj)

        # ?? do something to get states resolved??

        # Now we want to update the stored information
        datacache.ClearCache(save=True)

    def MapPartAs(self, name: str, toName: str):
        self.__alt_names[name] = toName


def MapPartAs(name: str, toName: str):
    '''
    Maps any reference of part name X to name Y
    '''
    glb.engine._part_manager.MapPartAs(name, toName)


api.register.add_global_object('MapPartNameAs', MapPartAs)
