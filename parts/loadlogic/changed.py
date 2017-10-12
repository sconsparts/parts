import base
from .. import requirement
from .. import glb
from ..pnode import section
from ..pnode import part
from .. import api
from .. import config
from .. import platform_info
from .. import node_helpers
from .. import datacache
from .. import dependent_ref
from .. import part_ref
from .. import target_type

import SCons

import os
import time

from SCons.Debug import logInstanceCreation


class SectionInfo(object):
    __slots__ = (
        '__weakref__',
        'section',
        'depend_esig_changed',
        'is_core_section',
        'changed',
        'requirements',
    )

    def __init__(self, section=None, depend_esig_changed=None, is_core_section=None):
        self.section = section
        self.depend_esig_changed = depend_esig_changed
        self.is_core_section = is_core_section
        self.changed = None
        self.requirements = None


class SectionInfoDict(dict):

    def __init__(self, onabsent):
        self.onabsent = onabsent

    def __missing__(self, key):
        self.onabsent(key)
        return self.get(key)


class Changed(base.Base):
    '''
    This loader will load any changed or new Part file so we can get updated information saved in our cache on what
    it would build. It then get the set of sections based on the targets provided and load any sections that define
    node that are out-of-date. Ideally we would just load the node information from cache and build it off that stored
    state as any information about the build context would have been loaded. Currently we have no way of doing this
    in SCons, because of this we need to load the file that defines the nodes we need to build, so they can build.
    Since this is lesser set of file than loading everything, this should greatly increase start up times.
    '''

    def __init__(self, targets, pmanager):
        if __debug__:
            logInstanceCreation(self)
        # these are the sections based on the target this is not the complete set of Sections we need to load
        # this is only the Set of node that map directly the the provides targets
        self.targets = targets

        # what we will load
        self.sections_to_load = set()
        # sections we know about that we might want to load
        self.known_sections = []
        # the part_manager object instance
        self.pmgr = pmanager

        # This is the information about all known section we have to look at
        # and some state about why we are loading or stuff we may need to check for
        # in later passes
        # will be in the form of {sec.ID:{datatype:info}}
        # TODO : Make section a simple dictionary when the issue with KeyError excption is resolved.
        self._section_info = SectionInfoDict(lambda key: self.AddSection(glb.pnodes.GetPNode(key)))
        # cache of known configuration
        self._knowncfgs = {}
        # cache of known builders
        self._knownbuilders = {}
        # cache of known nodes states
        self._known_nodes = {}

        # are we up-to-date... assume true till proven it false
        self._up_to_date = True

    def __call__(self):

        self.CheckTargets()

        # if we are not up-to-date we need to load the sections that are out of date
        if not self._up_to_date:
            # make sure we sort the list
            # so we avoid issues with custom data passing form
            # dependent Parts
            sections_to_load = [x for x in self.sections_to_load]
            sections_to_load.sort(section.scmp)
            total = len(sections_to_load)
            for cnt, s in enumerate(sections_to_load):
                api.output.console_msg("Loading {0:.1%} ({1}/{2} sections) \033[K".format((cnt * 1.0) / total, cnt, total))
                self.pmgr.LoadSection(s)

        return self._up_to_date

    def isNodeChanged(self, section_info, nodeid, _indent=1):
        # this does a recusive node check to see if
        # this node or it children are out of date
        # we go depth first as this overall allows us to
        # reduce the number of edge checks that may need to be do.
        try:
            # try to return known information about the state of this node
            tmp = self._known_nodes[nodeid]
            api.output.verbose_msg(['node_check_extra'], 'used cache for node {0}={1}'.format(nodeid, tmp))
            return tmp
        except KeyError:
            # we don't know about this node yet.. so figure it out

            # get stored info
            info = glb.pnodes.GetStoredNodeIDInfo(nodeid)
            # no info.. mean this is out of date
            # should not happen unless we are having state storing issues
            if not info:
                self._known_nodes[nodeid] = True
                api.output.verbose_msg(['node_check'], "{0} does not have any stored info found".format(nodeid))
                return self._known_nodes[nodeid]

            # get sources to this target node
            src_data = info.SourceInfo
            # for each source check to see if that is out of date
            api.output.verbose_msg(['node_check_extra'], '{0} Check Sources for {1}'.format(" " * _indent, nodeid))
            cache_load, file_load, src_out_of_date = set(), set(), set()
            for srcID, ninfo in src_data.iteritems():
                api.output.verbose_msg(['node_check_extra'], '{0} Source "{1}"'.format(" " * _indent, srcID))
                try:
                    # get the state of node given we have visited it already
                    tmp = self._known_nodes[srcID]
                except KeyError:
                    # don't have it yet. go down tree to get information
                    tmp = self.isNodeChanged(section_info, srcID, _indent + 1)

                    # Now we need to remember sections this source node is related to.
                    # Depending on the fact the source node is changed or not we put each
                    # section id into separate set object.
                    src_info = glb.pnodes.GetStoredNodeIDInfo(srcID)
                    if src_info:
                        (file_load if tmp else cache_load).update(
                            secID for secIDs in src_info.Components.itervalues()
                            for secID in secIDs
                            if secID != section_info.section.ID)
                    self._known_nodes[srcID] = tmp
                if tmp:
                    src_out_of_date.add(srcID)
                    # we are out of date because a src node is out of date
                    api.output.verbose_msg(
                        ['node_check'], "{0} is out of date because source node {1} say it is out of date".format(nodeid, srcID))

            if src_out_of_date:
                # Sections which nodes are changed will be loaded from *.parts files
                for secID in file_load:
                    section = glb.pnodes.GetPNode(secID)
                    if section:
                        self.SetToLoad(section, "{0} {1} out of date".format(', '.join(src_out_of_date),
                                                                             'is' if len(src_out_of_date) == 1 else 'are'))
                # Sections which nodes are not changed will be loaded from cache
                for secID in cache_load:
                    section = glb.pnodes.GetPNode(secID)
                    if section:
                        self.sections_to_load.add(section)
                        section.ReadState = glb.load_cache
                self._known_nodes[nodeid] = True

            # if everything is still good we want to check the edge inforation for this node
            try:
                # see if we have not already set the state of this node
                return self._known_nodes[nodeid]
            except KeyError:
                # don't have it yet. check to see if this node is out of date
                # based on it own edges
                self._known_nodes[nodeid] = glb.pnodes.hasNodeChanged(nodeid)
        return self._known_nodes[nodeid]

    def CheckNodes(self):
        # we want to get a set of section that are no out of date
        # and check there requirements to see if they have nodes that are
        # out of date and need to be rebuilt
        # this case we just need to see something is out of date and stop
        api.output.verbose_msg(['update_check'], "Started - Nodes checked")
        # get sections list that are still not out of date
        sectionIDs = []
        for secid, data in self._section_info.iteritems():
            if data.changed is None:
                sectionIDs.append(secid)

        # for each sections we want to check the nodes group of nodes that
        # matter for this section object
        total = len(sectionIDs)
        st = time.time()
        for cnt, secID in enumerate(sectionIDs):
            api.output.console_msg("Checking node groups {0:.1%} ({1}/{2}) \033[K".format((cnt * 1.0) / total, cnt, total))
            nodeIDs = []
            if self._section_info[secID].is_core_section:
                requirements = None
            else:
                requirements = self._section_info[secID].requirements
            section_info = self._section_info[secID]
            sec = section_info.section
            stored_data = sec.Stored

            if sec.AlwaysBuild:
                self.SetToLoad(sec, "AlwaysBuild was called in the section, force loading.")
                continue
            if requirements:
                # there are requirements we want to check for..
                # here we turn each requirement in to a Node
                # which we will use, via the node logic to see if it changed or out of date.
                for r in requirements:
                    if r.key in stored_data.ExportedRequirements:
                        nodeIDs.append('{0}::alias::{1}::{2}'.format(stored_data.Name, stored_data.PartID, r.key))
            else:
                # if this was None used the default requirement
                # this is actually the general node to build this the whole section
                # which is what we want here.
                nodeIDs = ['{0}::alias::{1}'.format(stored_data.Name, stored_data.PartID)]

            # for each "root node" we need to check if it is out-of-date
            for nodeID in nodeIDs:
                api.output.verbose_msg(['node_check_extra'], "check nodes group", nodeID)
                if self.isNodeChanged(section_info, nodeID):
                    self.SetToLoad(sec, "Node defined in this or dependent section is out of date")
                    break

        api.output.verbose_msg(['update_check'], "Finished - Nodes checked in {0} sec".format(time.time() - st))

    def CheckTargets(self):
        '''
        This is the main function that figures out what we want to process or not process based on the fact we have
        new part and exsiting part file have changed
        '''

        ########################################################################
        # When this is call we assume that all stored information is correct.

        # We have a set of Targets that we want to iterate on to get all sections we need to load
        # each target is either a tuple of a section object with group we want to build
        # or
        # is a single item that we view as a SCons node of some type that we will want
        # to try to get any sections that define it. Note if there are no sections
        # we just skip it as we assume the SConsruct defined everything for it in this case
        api.output.verbose_msg(['update_check'], "Starting - Context checks")

        st = time.time()
        for t in self.targets:
            try:
                # the group tells us if we are trying to build a subsection of the part
                # this gets mapped to an alias value of <section_type>::alias::<part id>::<group>
                # this will be needed later as this will be the core node we will want to check
                # for being up to date when we check for nodes
                sections, group = t
            except TypeError:
                # obj is either a Scons node or a section object
                # sections=self.pmgr.GetStoredSections(t)
                tmp = []
                self.pmgr.add_stored_node_info(t, tmp)
                sections = tmp
            # add section as known
            # Note we want to consider updating requirements via seeing if the group
            # maps to a requirement
            for i in sections:
                if i in self.targets:
                    self.AddSection(i, iscore=True)
                else:
                    self.AddSection(i)
            self.ProcessSections(sections)
        api.output.verbose_msg(['update_check'], "Finished - Context checked in {0} sec".format(time.time() - st))

        # at this point we should have set all top level sections that are out of date based
        # on changes that effect the environment or context of what we would build
        # now we want to see if there are any nodes that are out of date in any sections
        # that is still viewed up to date.

        self.CheckNodes()

        # check to see if we are up-to-date
        # if not we need to fill in sections in the tree of with the other sections that have to load
        # based on what we know is out of date.
        if not self._up_to_date:
            # we need to check that all sections that are out of date, are correctly
            # reflexed by the sections that dependon the them
            for sec in self.known_sections:
                self.DependentOutOfDate(sec)

            # at this point we need to make sure all parent Parts ( ie build sections of parent Parts)
            # are set to load. This will allow the last step of setting dependent to load from cache
            # to work correctly if a Parent Part has to load and it need to map some custom data
            # that we might not techincally need to build, but would need to allow the code to load
            # correctly
            for sec in set(self.sections_to_load):
                self.SetParentToLoad(sec)

            # now we want to do one last pass to mark all the dependent sections
            # that are out of date to be loaded from cache ( if not already set to
            # to be loaded from file)
            for sec in set(self.sections_to_load):
                self.SetDependsToCacheLoad(sec)

    def SetParentToLoad(self, sec):
        # For each of the parent ID's we need to set to load the build section
        stored = sec.Stored
        pobj = glb.pnodes.GetPNode(stored.PartID)
        for prtID in pobj.Stored.ParentIDs:
            pnode = glb.pnodes.GetPNode(prtID)
            tmp_sec = glb.pnodes.GetPNode(pnode.Stored.SectionIDs['build'])
            self.AddSection(tmp_sec)
            self.SetToLoad(tmp_sec, "{0} is parent of {1}".format(tmp_sec.ID, sec.ID))

    def DependentOutOfDate(self, sec):
        seen = set()

        def isDependentOutOfDate(self, sec):
            changed = self.isSectionMarkedChanged(sec)
            if sec.ID in seen:
                return changed

            seen.add(sec.ID)
            if changed:
                return True

            for dep_info in sec.Stored.DependsOn:
                dep_sec = glb.pnodes.GetPNode(dep_info.SectionID)
                if isDependentOutOfDate(self, dep_sec):
                    self.SetToLoad(sec, "{0} depends on another section that is out of date".format(sec.ID))
                    return True
            return False
        return isDependentOutOfDate(self, sec)

    def SetDependsToCacheLoad(self, sec):
        secIds = set(dep.SectionID for dep in sec.Stored.DependsOn)
        for dep_id in secIds:
            dep_sec = glb.pnodes.GetPNode(dep_id)
            pinfo = glb.pnodes.GetStoredPNodeIDInfo(dep_sec.Stored.PartID)
            if pinfo.ForceLoad:
                self.SetToLoad(dep_sec, "force_load was set to True")
                self.SetDependsToCacheLoad(dep_sec)
            elif dep_sec not in self.sections_to_load:
                dep_sec.ReadState = glb.load_cache
                self.sections_to_load.add(dep_sec)
                if dep_sec.ReadState == glb.load_cache:
                    api.output.verbose_msg(
                        ['update_check'], '{0} is set to be loaded from cache because it is a dependent of {1} which is out of date'.format(dep_sec.ID, sec.ID))

    def ProcessSections(self, sections):
        ''' Process all the sections to see if the context is out of date,
        add to the known set of sections
        and process all dependemts of the sections so we can get them added as well
        '''
        total = len(sections)
        cnt = 0
        for sec in sections:
            tmp = self.ProcessSection(sec)
            if tmp:
                self._up_to_date = False
            api.output.console_msg("Checking build context {0:.1%} ({1}/{2} ) \033[K".format((cnt * 1.0) / total, cnt, total))
            cnt += 1
        api.output.console_msg("Checking build context 100% ({0}/{1} ) \033[K".format(cnt, total))

    def ProcessSection(self, sec, requirements=None):

        # we want to test that the sections related configuration, builder and root part data
        # has not changed.
        if self.hasConfigContextChanged(sec):
            # if thesee cam back true, we want to set this to load
            self.SetToLoad(sec, "Configuration file changed")
        elif self.hasBuildContextChanged(sec):
            self.SetToLoad(sec, "File defining a builder changed")
        elif self.hasPartContextChanged(sec):
            self.SetToLoad(sec, "Define Context file or inputs changed")

        # we still have to continue to see if the dependancy changed
        # and add them to known sections to process
        return self.ProcessSectionDepends(sec, requirements) or not self._up_to_date

    def ProcessSectionDepends(self, sec, requirements):
        '''Process the depends information for a section to see if it is out of date
        It will also call, ProcessTargetSections() to recurse the depend sections
        and make sure these new dependent sections are known as items we will want to load
        or skip in some form.

        The depends information that is checked:
        1) is the dependednt section the same as the one we would have mapped
        2) given the dependent section is up-to-date ( not needed to be loaded)
            is the exports provided by the section changed
        3) Given the above is still ok, did a pattern that was called in the
            section have a possible change on disk that would casue a need
            for a rescan, and rebuild of stuff that the scan might have returned
        4) along the way if we see the dependent section is out of date we are out of date
            as well. hwoever we still have to check all dependents as we need to know
            everything we may have to load, as we don't store this information, since
            a simple change may map the section relationships.
        '''

        # this is hack to deal with a issue that needs a little more work
        # the issue is that the logic allows for a unit test to depend on other sections
        # via the depends arg. The issue is that we may load a unit test, but will not be
        # able to load a extra depends on a dependent unit test call. This is not needed to do the
        # build, but not loading it will cause data mapping  and stored state issues.
        # see if the utest target is being used..
        targets = SCons.Script.BUILD_TARGETS
        for t in targets:
            tmp = target_type.target_type(t)
            sep_len = len("::")
            if tmp.Section == 'utest':
                # if so we want to make see if we have a section utest that matches the build section
                # given this is a build section.
                if sec.Name == 'build':
                    if glb.pnodes.isKnownPNodeStored("utest::{0}".format(sec.Stored.PartID)):
                        tsec = glb.pnodes.GetPNode("utest::{0}".format(sec.Stored.PartID))
                        # if tsec is None:
                        #    1/0
                        self.ProcessSection(tsec)

        # end of hack

        for dep_info in sec.Stored.DependsOn:
            api.output.verbose_msg(['update_check_extra'], "ID:", sec.ID, "Dependson -> Name:", dep_info.PartName)
            # check to see that the if depends mapping we have is still valid
            if self.hasDependsMappingChanged(dep_info):
                if not self._section_info[sec.ID].depend_esig_changed:
                    self._section_info[sec.ID].depend_esig_changed = True

                # something changed to make us look at remapping this item
                new_depends = self.RemapDependent(dep_info)
                if new_depends.ID != dep_info.SectionID:
                    # this is a new mapping, so we need to do a few things
                    # 1) set this sectiond to load
                    self.SetToLoad(sec, "Dependancy change or was remapped to new value")
                    # 2) we need to modify our state to have this items in it instead
                    # of the existing information
                    dep_info.Update(new_depends)

            # get section object
            dep_sec = glb.pnodes.GetPNode(dep_info.SectionID)
            # add this section to know sections, as we no this is a valid section
            # and add the needed requirements we have on this

            self.AddSection(dep_sec)  # returns True is this was not Known yet
            if requirements is None:
                dep_requirements = dep_info.Requires
            else:
                # we want the common values both sets:
                dep_requirements = dep_info.Requires.intersection(requirements)

            req_changed = self.UpdateRequirements(dep_sec, dep_requirements)
            dep_sec_changed = False
            if req_changed:
                # if this is not known we need to do a full check on it
                dep_sec_changed = self.ProcessSection(dep_sec, dep_requirements)
            elif self.isSectionMarkedChanged(dep_sec):
                dep_sec_changed == True
            elif dep_info.ESig != dep_sec.Stored.ESig and req_changed:
                # elif dependancy exports changed we want to see if the requirements we
                # have really changed
                dep_sec_changed = self.hasDepedentTreeRequirementsChanged(sec, dep_info, dep_sec, dep_requirements)

            # now we want to process this sections
            if dep_sec_changed:
                # the depend section is viewed as out of date
                # so we are out of date
                self.SetToLoad(sec, "Dependent is out of date")
            elif self.hasPatternChanged(sec):
                # something on this disk that this section has a pattern scanning
                # looks like it may have changed. We will want to load to get changed
                # files
                self.SetToLoad(sec, "Files that we scan for may have changed")
        return self.isSectionMarkedChanged(sec)

    def SetToLoad(self, sec, reason):
        try:
            section_info = self._section_info[sec.ID]
        except KeyError:
            self._section_info[sec.ID] = section_info = SectionInfo(sec)
        if section_info.changed is None:
            api.output.verbose_msg(['update_check'], '{0} is out of date because: "{1}"'.format(sec.ID, reason))
            section_info.changed = reason
            sec.ReadState = glb.load_file
            self._up_to_date = False
            self.sections_to_load.add(sec)

    def isSectionMarkedChanged(self, sec):
        return bool(self._section_info[sec.ID].changed)

    def hasDependsMappingChanged(self, depends_info):
        ''' returns if the dependent map need to be remapped'''
        return depends_info.MappingSig != self.pmgr.StoredMappingSig(depends_info.PartName)

    def RemapDependent(self, depends_info):
        ''' Returns the new dependent section we would map to'''
        # use dependent info to create dependent_ref
        dref = dependent_ref.dependent_ref(part_ref.part_ref(depends_info.PartRefStr),
                                           depends_info.SectionName,
                                           depends_info.Requires
                                           )
        if not dref.hasStoredUniqueMatch:
            # we seem to have a problem, or bad set of parts being defined
            # raise expection to force loading everything
            raise StandardError  # replace with better type!!!
        # at the moment we assume we can find a good match, else
        # we map to a all loader
        return dref.StoredMatchingSections[0]

    def hasDepedentTreeRequirementsChanged(self, psec, info, sec, requirements):
        '''Test the requirements we have the dependancy tree
        Only has to recurse if the esig value is different, else we can ignore this
        '''
        dep_changed = False
        changed = False
        for dep_info in sec.Stored.DependsOn:
             # get section object
            dep_sec = glb.pnodes.GetPNode(dep_info.SectionID)
            if self._section_info[sec.ID].depend_esig_changed:
                # there was some dependent with a esig change so we want to recurse
                # to be safe
                dep_changed = self.hasDepedentTreeRequirementsChanged(sec, dep_info, dep_sec, requirements)
                if dep_changed:
                    changed = True
                    self.SetToLoad(sec, "Dependent is out of date")

        if changed:
            self.SetToLoad(sec, "Dependent is out of date")
        elif self.hasDependentExportsChanged(psec, info, sec, requirements):
            # something is what is being mapped in the dependent section
            #    # seems to have changed. We will want to load this.
            self.SetToLoad(psec, "Exported values from a dependent has changed")
            changed = True

        return changed

    def hasDependentExportsChanged(self, sec, depends_info, dep_sec, requirements):
        # We want to test to see if the main ESIG value is different
        # if it is the same nothing changed, else we need to see if what is different is
        # important to us based on requirements
        if depends_info.ESig != dep_sec.Stored.ESig:
            # something changed.. do we care?
            # we find out by testing the esigs with our set of rsigs
            # Which is to say we test each items we require from the
            # dependent with the matching esig value.
            return self.hasRequirementsChanged(sec, depends_info, dep_sec, requirements)
        return False

    def hasRequirementsChanged(self, sec, depends_info, dep_sec, requirements):

        reqs = requirements
        rsigs = depends_info.RSigs

        # we test each requirment signiture (rsig) we have and see if that data
        # in export data signiture (esig) has changed from our last run

        # for each requirement
        for req in reqs:
            # see if we require ( ie have a local need for the requirement)
            # as we might only need a sub set of the total requirements
            # in the locally defined requirements. for example need to test
            # REQ.Default.. but local requirement is only for REQ.HEADERS
            if req.key in rsigs.keys():
                if dep_sec.Stored.ESigs.get(req.key, '0') != rsigs.get(req.key, '0'):
                    self.SetToLoad(
                        sec, '{0} out-of-date! Dependent values "{1}" from "{2}" changed'.format(sec.ID, req.key, dep_sec.ID))
                    return True
        return False

    def hasPatternChanged(self, sec):
        # fill in with Pattern fixes
        return False

    def hasConfigContextChanged(self, sec):

        # test the files that define the configuration contexts
        # call method to get stored info.. also get info from "part" object is needed
        stored_cfg_data = sec.Stored.GetConfigContext()
        key = str(stored_cfg_data)
        try:
            return self._knowncfgs[key]
        except KeyError:
            # next we test the build context files
            for tool, file_list in stored_cfg_data.iteritems():
                    # get the files we would use in this run for a given tool
                cfg_files = config.get_defining_config_files(
                    sec.Stored.Part.Stored.Config,
                    tool,
                    platform_info.HostSystem(),
                    platform_info.SystemPlatform(sec.Stored.Part.Stored.TargetPlatform))
                # first check to see if these are the files we have cached
                # check to see that we have the same amount of files
                if len(cfg_files) != len(file_list):
                    api.output.verbose_msgf(
                        "update_check",
                        '{0} is out of date because the set of files defining configuration "{1}" for tool "{2}" are different.',
                        sec.ID, sec.Stored.Part.Stored.Config, tool
                    )
                    self._knowncfgs[key] = True
                    return True
                # test each file
                for file in file_list:
                    if file['name'] in cfg_files:
                        # this file is in the set of previous found files
                        # check if file has changed
                        if not node_helpers.node_up_to_date(file['name']):
                            api.output.verbose_msgf(
                                "update_check", '{0} is out of data because the file "{1}" that defines the configuration has changed', sec.ID, file['name'])
                            self._knowncfgs[key] = True
                            return True
                    else:
                        api.output.verbose_msgf(
                            "update_check",
                            '{0} is out of date because the set of files defining configuration "{1}" for tool "{2}" are different.\n The file "{3}" was not in set of: {4}',
                            sec.ID, sec.Stored.Part.Stored.Config, tool, file['name'], cfg_files

                        )
                        self._knowncfgs[key] = True
                        return True
        self._knowncfgs[key] = False
        return False

    def hasBuildContextChanged(self, sec):

        # test the files that define the builders
        # call method to get stored info.. also get info from "part" object is needed
        stored_bld_data = sec.Stored.GetBuilderContext()
        key = str(stored_bld_data)

        for bld in stored_bld_data:
            try:
                # Do we know of this item yet
                tmp = self._knownbuilders[bld['name']]
                # yes we do
                if tmp:  # is it out of date?
                    api.output.verbose_msgf(
                        "update_check",
                        '{0} is out of date because file "{1}" that defines builders has changed',
                        sec.ID, bld['name']
                    )
                    return tmp
            except KeyError:
                # we don't know of this file as of yet
                # next we test the build context file to see if this is good or bad
                if node_helpers.node_up_to_date(bld['name']) == False:
                    api.output.verbose_msgf(
                        "update_check",
                        '{0} is out of date because file "{1}" that defines builders has changed',
                        sec.ID, bld['name']
                    )
                    self._knownbuilders[bld['name']] = True
                    return True
                self._knownbuilders[key] = False
        # if we got here we loop through all builder items
        # and it all looks good, return there false to say no changes
        return False

    def hasPartContextChanged(self, sec):
        '''
        Test data about what was passed in to see if it is different
        Any New data that is passed in could change what the Parts does.
        This mean we need to reload it
        '''
        pinfo = glb.pnodes.GetStoredPNodeIDInfo(sec.Stored.PartID)
        if pinfo and pinfo.BuildTargets:
            return pinfo.BuildTargets <> set(
                target_type.target_type(target).Section for target in
                SCons.Script.BUILD_TARGETS)

        return False

    def UpdateRequirements(self, sec, requirements):
        # check to see the requirements are not set to load everything
        if self._section_info[sec.ID].is_core_section:
            return False  # nothing changed we need to have checked
        if requirements is None:
            requirements = requirement.Default()
        if self._section_info[sec.ID].requirements:
            curr_req = self._section_info[sec.ID].requirements
            # try to set the requirements
            # are requirements all existing in current requirements?
            if not requirements.issubset(curr_req):
                # Add what we have with what exists
                self._section_info[sec.ID].requirements |= requirements
                return True
            return False  # nothing changed we need to have checked
        else:
            self._section_info[sec.ID].requirements = requirements
        return True  # this is not known

    def AddSection(self, sec, iscore=False):

        if self._section_info.has_key(sec.ID):
            return False
        # Not known at the moment
        # set up basic structure
        self._section_info[sec.ID] = SectionInfo(
            section=sec,
            depend_esig_changed=False,
            is_core_section=iscore
        )
        # add to the sections we know about and will try to load
        # based on finail read state
        self.known_sections.append(sec)
        return True

    def process_depends(self, pobj, depends):
        pass
