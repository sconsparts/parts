from __future__ import absolute_import, division, print_function

import time

import parts.api as api
import parts.errors as errors
import parts.glb as glb
from SCons.Debug import logInstanceCreation

from . import base


class NoDepends(base.Base):  # task_master type
    '''
    This loads all target Parts files, and assume all dependants are up to date, loading them from cache
    This does not load "whole" parts ( ie the root and all sub-parts), only the part or sub-part the target maps to
    '''

    def __init__(self, targets, pmanager):
        if __debug__:
            logInstanceCreation(self)
        # set of sections to build
        # .. assume nodes are filtered out if ther did not expand to a section
        self.sections = []
        for i in targets:
            self.sections.extend(i[0])
        self.pmgr = pmanager

    @property
    def hasStored(self):
        return self.pmgr.hasStored

    @hasStored.setter
    def hasStored(self, value):
        if value == False:
            raise errors.LoadStoredError

    def next_task(self):
        t = self.__tasks[self.__i]
        if t is not None:
            self.__i += 1
        return t

    def stop(self):
        self.__stopped = True
        self.__i = -1

    @property
    def Stopped(self):
        return self.__stopped

    def cleanup(self):
        pass

    def _has_tasks(self):
        return self.__tasks != []

    def DefineTasksList(self):

        pass

    def __call__(self):

        sec_to_load = []
        # loop for each section
        for sec in self.sections:
            # get the stored info
            stored_data = sec.Stored
            if stored_data is None:
                # return False to signal there was a cache issue
                self.hasStored = False

            # set read state for this section
            sec.ReadState = glb.load_file
            if stored_data.Part.Stored.Parent:
                try:
                    tmp = glb.pnodes.GetPNode(stored_data.Part.Stored.Parent.Stored.SectionIDs[sec.Name])
                except KeyError:
                    tmp = glb.pnodes.GetPNode(stored_data.Part.Stored.Parent.Stored.SectionIDs['build'])
                if tmp not in self.sections:
                    self.sections.append(tmp)
            if sec.Name == 'utest':
                # this is a bit of a hack
                # but in general with classic formats (maybe new as well.. don't know yet)
                # we want to load the Build sections as well.
                tmp = glb.pnodes.GetPNode("build::{0}".format(stored_data.PartID))
                tmp.ReadState = glb.load_cache
                self.sections.append(tmp)

            # for each of the dependents we need to set the depends as cache load
            for dep in stored_data.DependsOn:
                dsec = glb.pnodes.GetPNode(dep.SectionID)
                dsec.ReadState = glb.load_cache
                if dsec not in sec_to_load:
                    sec_to_load.append(dsec)

            if sec not in sec_to_load:
                sec_to_load.append(sec)

        total = len(sec_to_load) * 1.0
        cnt = 0
        for sec in sec_to_load:
            if sec.ReadState == glb.load_cache:
                self.pmgr.LoadSection(sec)
                api.output.console_msg("Loading {0:.2%} ({1}/{2} sections) \033[K".format(cnt / total, cnt, total))
                cnt += 1

        for sec in sec_to_load:
            if sec.ReadState == glb.load_file:
                self.pmgr.LoadSection(sec)
                api.output.console_msg("Loading {0:.2%} ({1}/{2} sections) \033[K".format(cnt / total, cnt, total))
                cnt += 1

        return False
