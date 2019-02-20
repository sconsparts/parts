from __future__ import absolute_import, division, print_function

import parts.glb as glb
from SCons.Debug import logInstanceCreation


class dependent_info(object):
    ''' this class defines state we need for the section when we store dependancy information'''
    __slots__ = [
        '__part_ref_str',
        '__section_name',
        '__requires',
        '__rsigs',
        '__esig',
        '__sectionID',
        '__partID',
        '__part_name',
        '__mapping_sig'
    ]

    def __init__(self, dobj):
        if __debug__:
            logInstanceCreation(self)
        self.__part_ref_str = str(dobj.PartRef.Target)
        self.__section_name = dobj.SectionName
        self.__requires = dobj.Requires
        self.__rsigs = dobj.RSigs()
        self.__esig = dobj.Section.ESig()
        self.__sectionID = dobj.Section.ID
        self.__partID = dobj.Part.ID
        self.__part_name = dobj.Part.Name
        self.__mapping_sig = glb.engine._part_manager.MappingSig(dobj.Part.Name)

    @property
    def PartRefStr(self):
        return self.__part_ref_str

    @property
    def SectionName(self):
        return self.__section_name

    @property
    def Requires(self):
        return self.__requires

    @property
    def RSigs(self):
        return self.__rsigs

    @property
    def ESig(self):
        return self.__esig

    @property
    def SectionID(self):
        return self.__sectionID

    @property
    def PartID(self):
        return self.__partID

    @property
    def PartName(self):
        return self.__part_name

    @property
    def MappingSig(self):
        return self.__mapping_sig

    def Update(self, newsec):
        '''Update information about the new section we are mapping to now'''
        self.__sectionID = newsec.ID
        self.__partID = newsec.Part.ID
