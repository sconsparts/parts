
from __future__ import absolute_import, division, print_function



import copy
import hashlib
import os
import time

import SCons.Job
import SCons.Script
from SCons.Debug import logInstanceCreation

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
import parts.vcs as vcs
import parts.version as version
from parts.target_type import target_type


class part_manager(object):

    def __init__(self):
        if __debug__:
            logInstanceCreation(self)
        self.sections = glb.sections
        self.parts = {}  # a dictionary of all parts objects by there alias value
        self.__name_to_alias = {}  # a dictionary of a known Parts name and possible alias that match
        self.__to_map_parts = []  # stuff that needs to be mapped, else it is wasted space
        # used to help prevent wasting time on cases of incomplete cache data
        self.__hasStored = SCons.Script.GetOption("parts_cache")
        self.__part_count = 0  # number of parts we have defined..
        self.__root_part_count = 0  # number of Major parts/components we have defined..
        self.__loader = None
        glb.engine.CacheDataEvent += self.Store
        self.__new_parts = set()

        self.MappingEvent = events.Event()

    @property
    def Loader(self):
        return self.__loader

    def map_targets_stored_pnodes(self, targets):
        '''Turn the targets into a list of pnodes or Node ( given if can't be mapped to a Pnode) objects'''

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
                    # try:
                    #    for k,pobj in stored_name_to_alias[tn.Name].iteritems():
                    #        try:
                    #            name_matches[pobj.Stored.root.ID].add(pobj)
                    #        except KeyError:
                    #            name_matches[pobj.Stored.root.ID]=set([pobj])
                    # except KeyError:
                    #    pass
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
                    # and even possiblity not loading stuff ( ie in more complex cases of sub-parts with lots of Customization )
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
                                                       'Part {0} does not define a {1} section'.format(pobj.Stored.Name, tobj.Section))
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

        if (sec.LoadState < glb.load_file and sec.ReadState == glb.load_file):
            self.LoadPart(pobj)
            if pobj._remove_cache:
                sec._remove_cache = True
            else:
                sec.LoadState = glb.load_file  # should be set.. just being safe
        elif (sec.LoadState < glb.load_cache and sec.ReadState == glb.load_cache):
            self.LoadPart(pobj)  # load part from cache (function will do nothing if already loaded)
            if pobj._remove_cache:
                sec._remove_cache = True
            elif sec.LoadState < glb.load_cache:
                sec.LoadFromCache()  # load section from cache
                sec.LoadState = glb.load_cache

    def LoadPart(self, pobj):
        part_file_load_time = time.time()
        processed = False
        # see if this part is setup
        if pobj._remove_cache:
            api.output.verbose_msgf(['loading'], "{0} being ignored as it seems to not exist in the SConstruct anymore", pobj.ID)
        elif pobj.isSetup:
            # it is setup, so the parent has been read in
            if pobj.isLoading:
                api.output.verbose_msgf(['loading'], "{0} is already being loaded. Not Loading!", pobj.ID)
                return
            elif pobj.LoadState == glb.load_file:
                api.output.verbose_msgf(['loading'], "{0} was already loaded. Ignoring!", pobj.ID)
                return
            elif (pobj.LoadState < glb.load_file and pobj.ReadState == glb.load_file) or\
                not glb.pnodes.isKnownPNodeStored(pobj.ID) or\
                self.__hasStored == False or\
                    pobj.ForceLoad:
                # we want to read this Parts file. However this might be getting promoted form being loaded from cache to file
                # in this case we need to check that the parent has been read in if this is a subpart. If this is not the
                # case we want to read it in first and return. The reading of the parent should cause the sub-part to be
                # read, when the sub parts Part() call happens. This is mainly a "classic" format issue. The new format
                # should not have this problem.
                if not pobj.isRoot and pobj.Parent.LoadState < glb.load_file and not pobj.Parent.isLoading:
                    api.output.verbose_msgf(
                        ['loading'], "Trying to loading from file: {0},\n but the parent Part has not been read yet", pobj.ID)
                    self.LoadPart(pobj.Parent)
                    return

                # read in the data fully
                api.output.verbose_msgf(['loading'], "Loading from file: {0}", pobj.ID)
                pobj.isLoading = True
                pobj.UpdateReadState(glb.load_file)
                pobj.ReadFile()
                # move this?? This maps any unknown Part() calls that should be rebound to a parts object
                self._clean_unknown(pobj)
                # map the aliases
                # pobj._map_alias()
                # pobj._setup_sdk()
                # pobj._map_targets()

                # figure out if this part is new style or old style
                valid_sec = self.hasValidSection(pobj)
                if not pobj._hasTargetFiles() and valid_sec:
                    # new format
                    pobj.Format = 'new'
                    has_valid_sections = True
                elif pobj._hasTargetFiles() and valid_sec:
                    # mixed.. not sure what to do yet with this...
                    # print "mixed",pbj.Name
                    pass
                elif pobj._hasTargetFiles() and not valid_sec:
                    # old format
                    # if old format we have also processed the part
                    pobj.Format = 'classic'
                    pobj._setup_sdk()
                    pobj._map_targets()
                    # print "unknown",pobj.Name
                else:
                    # did not define anything to do?
                    # could be a root parts with subparts?
                    pobj.Format = 'unknown'
                    pobj._setup_sdk()
                    pobj._map_targets()
                    # print "unknown",pobj.Name
            #api.output.verbose_msg(['loading'],"{0:60}[{1:.2f} secs]".format(msg,(time.time()-part_file_load_time)))
            #api.output.console_msg(" Loading %3.2f%% %s \033[K"%((cnt/total*100),msg))
            # cnt+=1
                pobj.LoadState = glb.load_file
                processed = True
                pobj.isLoading = False

            elif pobj.LoadState < glb.load_cache and pobj.ReadState == glb.load_cache:  # not pobj.isRead and pobj.ReadState == glb.load_cache:
                api.output.verbose_msgf(['loading'], "Loading from cache: {0}", pobj.ID)
                pobj.isLoading = True
                pobj.LoadFromCache()
                self._add_part(pobj)
                pobj.LoadState = glb.load_cache
                pobj.isLoading = False
                processed = True

            elif pobj.ReadState == glb.load_none:
                api.output.verbose_msgf(['loading'], "not loading: {0}", pobj.ID)
        else:
            # we are trying to load some sub-part that has not had it parent read in yet
            # there are two cases for this parent..
            # 1)it will be read-in via load_cache
            # 2)it will be read in via load_file.
            # If the Parts parents is loaded yet, we need to load it
            policy = SCons.Script.GetOption("load_logic")
            if pobj.Stored.ParentID is None:
                # this part was probally removed
                api.output.verbose_msgf(['loading'], "not loading: {0} because it looks like it is not defined anymore", pobj.ID)
                self.__hasStored = False
                pobj._remove_cache = True

                if policy != 'all':
                    api.output.verbose_msgf(['loading'], "Trying to set load-logic to all logic", pobj.ID)
                    SCons.Script.Main.OptionsParser.values.load_logic = 'all'
                    # SCons.Script.SetOption("load_logic",'all')
                    raise errors.LoadStoredError
                return

            parent = glb.pnodes.GetPNode(pobj.Stored.ParentID)
            if parent.LoadState < parent.ReadState:
                try:
                    self.LoadPart(parent)
                except errors.LoadStoredError:
                    raise
            # check to see if the whole parts seems to be missing
            if parent._remove_cache:
                pobj._remove_cache = True
                api.output.verbose_msgf(
                    ['loading'], "{0} being ignored as {1} seems to not exist in the SConstruct anymore", pobj.ID, pobj.Stored.RootID)
                return

            # Given that it is read at this point. we need to check to see if we are read
            # given that parent should have loaded.. we should be loaded as well
            # if we are not and we are to be read in as cache ( what we should see if not read-in yet)
            # we want to load this part from cache

            # At this point we should be setup at the very least, if not loaded
            # if the parent was loaded from cache we might not be loaded yet
            if pobj.LoadState < glb.load_cache and pobj.ReadState == glb.load_cache:
                api.output.verbose_msgf(['loading'], "Loading From cache: {0}", pobj.ID)
                pobj.LoadFromCache()
                self._add_part(pobj)
                pobj.LoadState = glb.load_cache
                processed = True
            # it is possible a loader gave us a part we want to ignore
            elif pobj.ReadState == glb.load_none:
                api.output.verbose_msgf(['loading'], "not loading: {0}", pobj.ID)
            elif pobj.LoadState == glb.load_none:
                # if we get here the most likely case is this is a complex part with lots of subparts
                # check to see if the parent still defined this sub-part, it may have been removed or renamed
                if pobj.ID in parent.Stored.SubPartIDs and not parent.isLoading:
                    # This appears to be so. We want to mark this data to be removed so we don't look for it again
                    api.output.verbose_msgf(
                        ['loading'], "Can't load {0} as this is a subpart does not appear to exist in the parent anymore.", pobj.ID)
                    pobj._remove_cache = True

                elif parent.isLoading:
                    # we most likely have a case in which a sub-part that has yet to be read in is being force read
                    # as it is in a depends of a sub-part that was defined before it in the Parts file
                    # there is nothing we can do with this given the classic format. so we punt and hope for the best
                    if policy != 'all':
                        api.output.verbose_msgf(['loading'], "Trying to set load-logic to all logic", pobj.ID)
                        SCons.Script.Main.OptionsParser.values.load_logic = 'all'
                        self.__hasStored = False
                        # SCons.Script.SetOption("load_logic",'all')
                        raise errors.LoadStoredError
                    else:
                        api.output.verbose_msgf(
                            ['loading'], "Can't load {0} as parent part is still loading. Skipping, May cause failures", pobj.ID)

                else:

                    if policy != 'all':
                        api.output.verbose_msgf(['loading'], "Can't load {0} Not sure why? Falling back", pobj.ID)
                        api.output.verbose_msgf(['loading'], "Trying to set load-logic to all logic", pobj.ID)
                        SCons.Script.Main.OptionsParser.values.load_logic = 'all'
                        self.__hasStored = False
                        # SCons.Script.SetOption("load_logic",'all')
                        raise errors.LoadStoredError
                    else:
                        api.output.verbose_msgf(['loading'], "Can't load {0} Not sure why? Skipping, May cause failures", pobj.ID)
                return

        if processed:
            api.output.verbose_msgf(['loading'], "Loaded {0:45}[{1:.2f} secs]", pobj.ID, (time.time() - part_file_load_time))

    def _define_sub_part(self, env, alias, parts_file, mode=[], vcs_type=None,
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

        if vcs_type is None:
            vcs_type = parent_part.Vcs
            new_kw['CHECK_OUT_DIR'] = new_kw['VCS'] = parent_part.Env.subst("$CHECK_OUT_DIR")
        if package_group is None:
            package_group = parent_part.PackageGroup
        if mode == []:
            mode = parent_part.Mode
        new_kw.update(kw)
        if 'parent_part' in new_kw:
            del new_kw['parent_part']
        new_append.update(append)
        new_prepend.update(prepend)
        tmp = glb.pnodes.Create(pnode.part.part, alias=alias, file=parts_file, mode=mode, vcs_t=vcs_type,
                                default=default, append=new_append, prepend=new_prepend,
                                create_sdk=create_sdk, package_group=package_group,
                                parent_part=parent_part, **new_kw)

        # make sure that if the parent is being loaded
        # that we load this from cache
        if parent_part.ReadState == glb.load_file and tmp.ReadState == glb.load_none:
            tmp.UpdateReadState(glb.load_cache)

        # setup new object
        # tmp._setup_()
        # add to set of known parts
        if tmp.isSetup:
            # see if this should be readin
            self._add_part(tmp)
            self.LoadPart(tmp)
        else:
            print(tmp.ID, "is NOT SETUP!!!!!!!!")

        # store setup state if this is a read cache or ignore case, as it might need to load latter as a file
        # and we will not be able to get the orginal state to "reinit" this component
        if tmp.ReadState != glb.load_file:
            tmp_args = new_kw
            tmp_args.update({
                            'alias': alias,
                            'file': parts_file,
                            'mode': mode,
                            'vcs_t': vcs_type,
                            'default': default,
                            'append': new_append,
                            'prepend': new_prepend,
                            'create_sdk': create_sdk,
                            'package_group': package_group,
                            'parent_part': parent_part
                            })
            tmp._cache["init_state"] = tmp_args

        if tmp.LoadState == glb.load_cache:
            # If this is the case we need to make sure the sections are processed
            for secid in tmp.Stored.SectionIDs.values():
                s = glb.pnodes.GetPNode(secid)
                if s.ReadState == glb.load_cache:
                    s.LoadFromCache()  # load section from cache
                    s.LoadState = glb.load_cache

        return tmp

    def map_scons_target_list(self, uptodate):
        ''' here we try to map the Parts target values to values SCons can build'''

        stored_data = datacache.GetCache("part_map")
        # trying to translate based on everything being read in
        new_list = []  # the new target list
        skip_list = []

        def _add_list(_nodestr, orginal_str, target_obj):
            '''
            This is a helper funtions to test if the node is known and or possibly valid
            before we try to add the node to the target list
            '''

            # if glb.pnodes.isKnownNodeStored(_nodestr):
            #    pass
            # elif not glb.pnodes.isKnownNode(_nodestr) and not target_obj.hasAlias:
            #    # This is not defined or known in the cache
            #    # since it is not defined or known to be a valid target we error
            #    api.output.error_msgf("{0} is an invalid target",orginal_str)#,show_stack=False)

            new_list.append(_nodestr)

        api.output.verbose_msgf(['loading'], "Orginal BUILD_TARGETS: {0}", SCons.Script.BUILD_TARGETS)
        for t in SCons.Script.BUILD_TARGETS:
            tobj = target_type(t)
            # first see if this is ambiguous
            if tobj.isAmbiguous:
                # we are not sure
                # first we try to see if the name can be matched
                ta = target_type("alias::" + str(t))
                tn = target_type("name::" + str(t))
                if self.__name_to_alias.get(tn.Name):
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
                basestr = "{0}::alias::{1}".format(concept, tobj.Alias)
                if tobj.hasGroups:
                    for grp in tobj.Groups:
                        basestr = "{0}::{1}".format(basestr, grp)
                        if tobj.isRecursive:
                            basestr = "{0}::".format(basestr)
                        _add_list(basestr, t, tobj)
                else:
                    if tobj.isRecursive:
                        basestr = "{0}::".format(basestr)
                    _add_list(basestr, t, tobj)

            elif tobj.Name:
                # This case can have multipul matches
                # get a list of known alias that have this name
                alias_lst = self.__name_to_alias.get(tobj.Name)

                if alias_lst is None:
                    # we might have a case in which this item is not loaded
                    # we need to check that we have a cache and that this item
                    # defined here. Given that we trust that it safe to ignore
                    if stored_data is not None and\
                       stored_data['name_to_alias'].get(tobj.Name, None) is not None:
                        # If this is true we can say we know that we tried to load this part
                        # but it was probally skipped by the load logic for some reason
                        # and we should ignore it
                        api.output.verbose_msgf(
                            ['loading'], 'Skipping target "{0}" as it is believe to have been skipped by the load logic manager', t)
                        skip_list.append(t)
                        continue
                    # error we don't have a target called this to build
                    api.output.error_msg("Unknown name: %s" % (tobj.Name), show_stack=False)
                else:
                    pobj_lst = [self._from_alias(i) for i in alias_lst]
                # filter out any of these that don't match the properties
                pobj_lst = self.reduce_list_from_target(tobj, set(pobj_lst))
                if not pobj_lst:
                    api.output.error_msg('"%s" did not map to any defined Parts' % t)
                for pobj in pobj_lst:
                    basestr = "{0}::alias::{1}".format(concept, pobj.Alias)
                    if tobj.hasGroups:
                        for grp in tobj.Groups:
                            basestr = "{0}::{1}".format(basestr, grp)
                            if tobj.isRecursive:
                                basestr = "{0}::".format(basestr)
                            _add_list(basestr, t, tobj)
                    else:
                        if tobj.isRecursive:
                            basestr = "{0}::".format(basestr)
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

    def ProcessParts(self):
        '''
        This function will process all the Parts object based on the targets
        '''

        #######
        # update the disk
        # is everything up to date on disk update file on disk?
        # if not we need to update it
        if SCons.Script.GetOption('update'):
            api.output.print_msg("Updating disk")
            self.UpdateOnDisk(list(self.parts.values()))
            api.output.print_msg("Updating disk - Done")

        # self.UpdateStoredState()
        # return
        if len(SCons.Script.BUILD_TARGETS) == 1 and SCons.Script.BUILD_TARGETS[0] == "extract_sources":
            return

        skip_update_check = True
        nodes_up_to_date = True
        has_valid_sections = False
        targets = SCons.Script.BUILD_TARGETS
        # check to see that we even have targets to process
        if targets == []:
            return
        sections_to_process = []
        nodes = []

        # this is temp hack to get the code out.. with the load logic re factors
        # at the moment any part file "change" mean load everything
        if self.__hasStored:
            if self.ChangedParts or self.NewRootParts:
                self.__hasStored = False

        if self.__hasStored:
            # map target to a part alias or a scons node via mapping node info from our DB of all known nodes
            try:
                tmp = self.map_targets_stored_pnodes(targets)

                # check to see if any SCons nodes in the targets are out of date
                if tmp:
                    # break up the returned data into sections, and SCons nodes
                    sections_to_process, nodes = tmp

            except errors.LoadStoredError:
                self.__hasStored = False

            api.output.verbose_msg(['loading'], "reduced sections to process=", [([k.ID for k in i], j)
                                                                                 for i, j in sections_to_process])

            # SCons.Script.GetOption("early_exit")
            if self.__hasStored and sections_to_process:

                # If we have stored data we will try to do some logic to reduce startup time
                # by doing some form of reduce reads based on what we know is up-to-date or not

                policy = SCons.Script.GetOption("load_logic")
                if policy == 'default':
                    policy = 'min'
                if SCons.Script.GetOption("interactive") and policy != "unsafe":
                    policy = 'all'

                api.output.verbose_msgf(['loading'], "Using load logic: {0}", policy)
                if policy == 'target' or glb.engine._build_mode == 'clean' or glb.engine._build_mode == 'question':
                    # fully load all direct depends ( no cache loads )
                    loader = loadlogic.target.Target(sections_to_process, self)

                elif policy == 'min':
                    # Load all Part that are out of date, immediate depends from cache, ignore everything else
                    loader = loadlogic.changed.Changed(sections_to_process, self)

                elif policy == 'unsafe':
                    # load only the sections assume everything is up to date
                    loader = loadlogic.nodepends.NoDepends(sections_to_process, self)
                    api.output.warning_msg(
                        'Load logic case of "unsafe" is being used!\n'
                        ' All dependents are assumed up-to-date!\n'
                        ' If this is not the case the build may be incorrect or fail!', show_stack=False)

                elif policy == 'all':
                    # load everything
                    self.__hasStored = False
                    loader = loadlogic.all.All(self)
            else:
                api.output.verbose_msg(['loading'], "Loading everything as the given targets are unknown")
                self.__hasStored = False
                loader = loadlogic.all.All(self)

        else:
            if self.ChangedParts or self.NewRootParts:
                api.output.verbose_msg(['loading'], "Loading everything as there are changes in the Part files")
            else:
                api.output.verbose_msg(['loading'], "Loading everything as there is no cache")
            self.__hasStored = False
            loader = loadlogic.all.All(self)

        self.__loader = loader
        try:
            up_to_date = self.__loader()
        except errors.LoadStoredError:
            api.output.verbose_msg(['loading'], "Loading everything as changes seem to be complex")
            self.__hasStored = False
            self.__loader = loadlogic.all.All(self)
            up_to_date = self.__loader()

        if up_to_date and nodes_up_to_date:
            api.output.verbose_msg(['loading'], "Everything is up-to-date!")
            api.output.print_msg("Targets are up to date!")
            glb.engine.UpToDateExit()

        self.map_scons_target_list(up_to_date)
        glb.pnodes.clear_node_states()

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
            if target.orginal_string not in ['all', '.']:
                api.output.warning_msg(
                    'Target "%s" is unknown to Parts, it may be known to SCons. Force reading all data' % target.orginal_string)
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

    def hasValidSection(self, part):
        '''
        This function test to see if the Part has state the show it has a valid section defined
        '''
        return part._has_valid_sections()

    def UpdateOnDisk(self, part_set=None):
        ''' Update any parts that need to be updated on disk

        @param part_set The set of Part to see if they are up-to-date, if test all Parts
        '''
        # we need to see if any part needs to be checked out or updated
        # loop each part and ask it need to be updated
        p_list = vcs.task_master.task_master()
        s_list = vcs.task_master.task_master()
        if part_set is None:
            part_set = list(self.parts.values())
        update_set = set([])
        for p in part_set:
            # if so add to queue for checkout
            vcsobj = p.Vcs
            if vcsobj.NeedsToUpdate():
                # we check to see if the vcs object allow for the
                # parallel checkout policy.
                update_set.add(p)
                if vcsobj.AllowParallelAction():
                    p_list.append(vcsobj)
                else:
                    s_list.append(vcsobj)
            elif not vcsobj.CacheFileExists:
                update_set.add(p)

        def post_vcs_func(jobs, tm):
            if jobs.were_interrupted():
                tm.ReturnCode = 3
                api.output.error_msg("Updating of disk was interrupted!", show_stack=False)
            elif tm.Stopped:
                tm.ReturnCode = 4
                api.output.error_msg("Errors detected while updating disk!", show_stack=False)

        # checkout anything in the queue
        try:
            if p_list._has_tasks():
                # get value for level of number of concurrent checkouts
                vcs_j = SCons.Script.GetOption('vcs_jobs')
                if vcs_j == 0:
                    vcs_j = SCons.Script.GetOption('num_jobs')
                p_list.append(None)
                jobs = SCons.Job.Jobs(vcs_j, p_list)
                jobs.run(postfunc=lambda: post_vcs_func(jobs, p_list))
            if s_list._has_tasks():
                p_list.append(None)
                jobs = SCons.Job.Jobs(1, s_list)
                jobs.run(postfunc=lambda: post_vcs_func(jobs, s_list))
        except:
            if p_list.ReturnCode:
                glb.engine.def_env.Exit(p_list.ReturnCode)
            if s_list.ReturnCode:
                glb.engine.def_env.Exit(p_list.ReturnCode)
            glb.engine.def_env.Exit(2)
        finally:
            for p in update_set:
                p.Vcs.PostProcess()
            datacache.SaveCache(key='vcs')

    def MappingSig(self, name):

        md5 = hashlib.md5()
        for i in self.__name_to_alias[name]:
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

    def _clean_unknown(self, known_pobj):
        for i in self.__to_map_parts:
            if i.Name == known_pobj.Name and\
                i.Version == known_pobj.Version and\
                    i._kw.get('TARGET_PLATFORM', glb.engine.def_env['TARGET_PLATFORM']) == known_pobj.Env['TARGET_PLATFORM']:
                known_pobj._merge(i)
                self.__to_map_parts.remove(i)
                break

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
                        "  Matching Attibute: {key} Values: {val} with {tval}",
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
                        "  Matching Attibute: {key} Values: {val} Based on {tval}",
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
                        "  Matching Attibute: {key} Values: {val} with {tval}",
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
                        "  Matching Attibute: {key} Values: {val} with {tval}",
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
                    # empty set, or the empty set was testing on something else to reduce ambigous matches
                    try:
                        api.output.trace_msgf(
                            "reduce_target_mapping",
                            "  Matching Emvironment Variable: {key} Values: {val} with {tval}",
                            key=key,
                            val=val,
                            tval=pobj.Env[key]
                        )

                        if util.isList(pobj.Env[key]):
                            api.output.trace_msgf("reduce_target_mapping", "  Variable is a list in the Environment")
                            val_list = val.split(',')
                            api.output.trace_msgf("reduce_target_mapping",
                                                  "  Testing that Enviornment variable contains all values in {0}", val_list)
                            for v in val_list:
                                if v not in pobj.Env[key]:
                                    match = False
                                    break
                        else:
                            api.output.trace_msgf("reduce_target_mapping",
                                                  "  Variable is not a list in the environment Environment")
                            # if both cases are false then we have a failure
                            if pobj.Env[key] != val and str(pobj.Env[key]) != v:
                                api.output.trace_msgf("reduce_target_mapping", "   Removing Part {0}", pobj.ID)
                                match = False
                    except KeyError:
                        match = False
                if not match:
                    api.output.trace_msgf("reduce_target_mapping", "  Removing Part {0}", pobj.ID)
                    break

            if match:
                ret_lst.append(pobj)
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
                                          "  Matching Attibute: {0} Values:{1} {2}", k, v, pobj.Stored.Version)
                    if util.isString(v):
                        v = version.version_range(v + '.*')
                    if pobj.Stored.Version not in v:
                        api.output.trace_msgf("stored_reduce_target_mapping", "  Removing Part {0}", pobj.ID)
                        part_lst.remove(pobj)
                elif k in ['target', 'target-platform', 'target_platform']:
                    api.output.trace_msgf("stored_reduce_target_mapping",
                                          "  Matching Attibute: {0} Values:{1} {2}", k, v, pobj.Stored.TargetPlatform)
                    if pobj.Stored.TargetPlatform != v:
                        api.output.trace_msgf("stored_reduce_target_mapping", "  Removing Part {0}", pobj.ID)
                        part_lst.remove(pobj)
                elif k in ['platform_match']:
                    api.output.trace_msgf("stored_reduce_target_mapping", "  Matching Attibute: {0} Values:{1} {2} Types:{3} {4}", k, v, pobj.Stored.PlatformMatch, type(
                        v), type(pobj.Stored.PlatformMatch))
                    if pobj.Stored.PlatformMatch != v:
                        api.output.trace_msgf("stored_reduce_target_mapping", "  Removing Part {0}", pobj.ID)
                        part_lst.remove(pobj)
                elif k in ['cfg', 'config', 'build-config', 'build_config']:
                    # weak... make better code for this case
                    if pobj.Stored.ConfigMatch:
                        api.output.trace_msgf("stored_reduce_target_mapping", "  Matching Attibute: {0} Values:{1}", k, v)
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
        return self.__name_to_alias.get(name, set([]))

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
                if v.LoadState == glb.load_file:  # might need to relook at this case when we get new formats working
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
                        class wrapper(object):

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
