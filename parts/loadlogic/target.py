
from .. import glb
import base
from ..pnode import part
from .. import api

import time

from SCons.Debug import logInstanceCreation

class Target(base.Base): #task_master type
    '''
    Try to load on items related to the target, even if ther are out of date
    '''
    def __init__(self,targets,pmanager):
        if __debug__: logInstanceCreation(self)
        # set of sections to build
        #.. assume nodes are filtered out if ther did not expand to a section
        self.sections= []
        for i in targets:
            self.sections.extend(i[0])
        self.pmgr=pmanager
        self._section_from_cache=set() # all the section we need to load from cache
        self._parts_to_read=set() # all the parts we have to readin


    @property
    def hasStored(self):
        return self.pmgr.hasStored

    @hasStored.setter
    def hasStored(self,value):
        if value==False:
            raise errors.LoadStoredError

    def next_task(self):
        t = self.__tasks[self.__i]
        if t is not None:
            self.__i += 1
        return t

    def stop(self):
        self.__stopped=True
        self.__i= -1

    @property
    def Stopped(self):
        return self.__stopped

    def cleanup(self):
        pass

    def _has_tasks(self):
        return self.__tasks != []

    def DefineTasksList(self):

        if sec.TagDirectDependAsLoad()==False:
            self.pmgr.hasStored=False
            return False

        for pobj in self.pmgr.parts.values():
            if pobj.ReadState==glb.load_file:
                self.__tasks.append(load_parts_task(pobj,self.pmgr,self))


    def __call__(self):
        # we are force loading files here so
        # we can exit early
        for sec in self.sections:
            if sec.TagDirectDependAsLoad(self.pmgr)==False:
                self.pmgr.hasStored=False
                return False

        parts_to_load=self.pmgr.parts.values()
        parts_to_load.sort(part.pcmp)
        for pobj in parts_to_load:
            if pobj.ReadState==glb.load_file:
                self.pmgr.LoadPart(pobj)
        return False
