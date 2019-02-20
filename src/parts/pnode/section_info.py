from __future__ import absolute_import, division, print_function

import parts.glb as glb
import parts.pnode.stored_info as stored_info


class section_info(stored_info.stored_info):
    """description of class"""
    __slots__ = [
        '__name',                   # name of the section - good after file read
        '__partID',                 # the part ID of the part holding the section - good after file read
        '__exports',                # all exported data for this sectiond - good after all part files are processed
        # sig data for each item we export ( faster to test than testing values of
        # export table) - good after all part files are processed
        '__esigs',
        # sig data for all items we export ( faster to test than testing values of
        # export table) - good after all part files are processed
        '__esig',
        # info on what we dependon - good after all part files are processed ( only for info that maps what was resolved)
        '__dependson',
        # items we want to make alias of for cache loading as these items are
        # mapped as dependent alias for the main target ( re look at this) - good
        # after file process
        '__exported_requirements',
        '__user_env_diff',          # info about what is different with the environment vs the given default - good after file process
        '__installed_files',        # List of (<node id>, <package metatag>) pairs
    ]

    def __init__(self):
        self.__name = ''
        self.__partID = None
        self.__exports = {}
        self.__esigs = {}
        self.__esig = None
        self.__dependson = []
        self.__exported_requirements = list()
        self.__user_env_diff = {}
        # self.build_context=[]
        # self.config_context=[]

    @property
    def Name(self):
        return self.__name

    @Name.setter
    def Name(self, val):
        self.__name = val

    @property
    def PartID(self):
        return self.__partID

    @PartID.setter
    def PartID(self, val):
        self.__partID = val

    @property
    def Exports(self):
        return self.__exports

    @Exports.setter
    def Exports(self, val):
        self.__exports = val

    @property
    def ESigs(self):
        return self.__esigs

    @ESigs.setter
    def ESigs(self, val):
        self.__esigs = val

    @property
    def ESig(self):
        return self.__esig

    @ESigs.setter
    def ESig(self, val):
        self.__esig = val

    @property
    def DependsOn(self):
        return self.__dependson

    @DependsOn.setter
    def DependsOn(self, val):
        self.__dependson = val

    @property
    def ExportedRequirements(self):
        return self.__exported_requirements

    @ExportedRequirements.setter
    def ExportedRequirements(self, val):
        self.__exported_requirements = val

    @property
    def UserEnvDiff(self):
        return self.__user_env_diff

    @UserEnvDiff.setter
    def UserEnvDiff(self, val):
        self.__user_env_diff = val

    def GetConfigContext(self):
        '''This will get the config context for a given section
        and merge with the parts version as needed'''

        # currently we just use the Parts version
        return self.Part.Stored.Root.Stored.ConfigContext

    def GetBuilderContext(self):
        '''This will get the builder context for a given section
        and merge with the parts version as needed'''

        # currently we just use the Parts version
        return self.Part.Stored.Root.Stored.BuildContext

    @property
    def Part(self):
        return glb.pnodes.GetPNode(self.PartID)

    @property
    def InstalledFiles(self):
        try:
            return self.__installed_files
        except AttributeError:
            return tuple()

    @InstalledFiles.setter
    def InstalledFiles(self, value):
        # To validate the value we iterate by its items and unpack each one
        self.__installed_files = tuple(
            (node_id, package_tag) for (node_id, package_tag) in value)
