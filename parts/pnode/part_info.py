import stored_info
from .. import glb
from .. import platform_info
from .. import common

class part_info(stored_info.stored_info):
    """description of class"""
    __slots__=[
        '__name',                # name of part -- good after file read
        '__short_name',          # short name of part (just the end piece) - good after file read
        '__ID',                  # the ID - good after file read
        '__short_alias',         # the short alias ( the end value of the ID) might remove - good after file read
        '__version',             # the version - good after file read
        '__rootID',              # the root part ID ( is self if no subparts) - good after file read
        '__target_platform',     # the target platform we are building for - good after file read
        '__config',              # the configuration ( debug, release, etc) - good after file read
        '__platform_match',      # any special matching requirments set by this part - good after file read
        '__config_match',        
        '__package_group',       # the package group this was mapped to - good after file read
        '__mode',                # any mode information - good after file read
        '__subpartIDs',          # IDs of the subparts if any - good after file read
        '__parentIDs',           # chain of all Parent part IDs.. A.B.C will have [a,b] - good after file read
        '__parentID',            # the direct Parent ID, None if no parent - good after file read
        '__sectionIDs',          # IDs of all defined sections in this Part - good after file read
        '__file',                # information about file - good after file read
        '__src_path',            # information of path that contains part file - good after file read
        '__build_context',       # Information off all file that defined builders that had been called in any section of this Part - good after file read ( or after queue processing)
        '__config_context',      # Information off all file that defined configuration information that had been called in any section of this Part - good after file read
        '__force_load',          # does this need to be loaded for file if it is a dependancy, not cache - good after file read
        '__kw',                  # random stuff passed in - good after file read
        '__vcs_cache_filename',  # information about cache file that has information about VCS state for this Parts, if any. - good after file read
        '__build_targets',       # How does this Part care about SCons.Script.BUILD_TARGET values
    ]
    def __init__(self):

        self.__name=''
        self.__short_name=''
        self.__ID=''
        self.__short_alias=''
        self.__version=None
        self.__rootID=None
        self.__target_platform=''
        self.__config=''
        self.__platform_match=''
        self.__config_match=True
        self.__package_group=''
        self.__mode=[]
        self.__subpartIDs=set()
        self.__parentIDs=[]
        self.__parentID=None
        self.__sectionIDs={}
        self.__file={} # file.ninfo plus name
        self.__src_path=None # Node
        self.__build_context=[]
        self.__config_context=[]
        self.__force_load=False
        self.__kw={}
        self.__vcs_cache_filename=None


    @property
    def Name(self):
        return self.__name
    @Name.setter
    def Name(self,val):
        self.__name=val

    @property
    def ShortName(self):
        return self.__short_name
    @ShortName.setter
    def ShortName(self,val):
        self.__short_name=val

    @property
    def ID(self):
        return self.__ID
    @ID.setter
    def ID(self,val):
        self.__ID=val

    @property
    def ShortID(self):
        return self.__short_alias
    @ShortID.setter
    def ShortID(self,val):
        self.__short_alias=val

    @property
    def Version(self):
        return self.__version
    @Version.setter
    def Version(self,val):
        self.__version=val

    @property
    def RootID(self):
        return self.__rootID
    @RootID.setter
    def RootID(self,val):
        self.__rootID=val

    @property
    def TargetPlatform(self):
        return self.__target_platform
    @TargetPlatform.setter
    def TargetPlatform(self,val):
        self.__target_platform=val

    @property
    def Config(self):
        return self.__config
    @Config.setter
    def Config(self,val):
        self.__config=val

    @property
    def PlatformMatch(self):
        return self.__platform_match
    @PlatformMatch.setter
    def PlatformMatch(self,val):
        self.__platform_match=val

    @property
    def ConfigMatch(self):
        return self.__config_match
    @ConfigMatch.setter
    def ConfigMatch(self,val):
        self.__config_match=val

    @property
    def PackageGroup(self):
        return self.__package_group
    @PackageGroup.setter
    def PackageGroup(self,val):
        self.__package_group=val

    @property
    def Mode(self):
        return self.__mode
    @Mode.setter
    def Mode(self,val):
        self.__mode=common.make_list(val)

    @property
    def SubPartIDs(self):
        return self.__subpartIDs
    @SubPartIDs.setter
    def SubPartIDs(self,val):
        self.__subpartIDs=val

    @property
    def ParentIDs(self):
        return self.__parentIDs
    @ParentIDs.setter
    def ParentIDs(self,val):
        self.__parentIDs=val

    @property
    def ParentID(self):
        return self.__parentID
    @ParentID.setter
    def ParentID(self,val):
        self.__parentID=val

    @property
    def SectionIDs(self):
        return self.__sectionIDs
    @SectionIDs.setter
    def SectionIDs(self,val):
        self.__sectionIDs=val

    @property
    def File(self):
        return self.__file
    @File.setter
    def File(self,val):
        self.__file=val

    @property
    def SrcPath(self):
        return self.__src_path
    @SrcPath.setter
    def SrcPath(self,val):
        self.__src_path=val

    @property
    def BuildContext(self):
        return self.__build_context
    @BuildContext.setter
    def BuildContext(self,val):
        self.__build_context=val

    @property
    def ConfigContext(self):
        return self.__config_context
    @ConfigContext.setter
    def ConfigContext(self,val):
        self.__config_context=val

    @property
    def ForceLoad(self):
        return self.__force_load
    @ForceLoad.setter
    def ForceLoad(self,val):
        self.__force_load=val

    @property
    def kw(self):
        return self.__kw
    @kw.setter
    def kw(self,val):
        self.__kw=val

    @property
    def VcsCacheFilename(self):
        return self.__vcs_cache_filename
    @VcsCacheFilename.setter
    def VcsCacheFilename(self,val):
        self.__vcs_cache_filename=val

    @property
    def Parent(self):
        return glb.pnodes.GetPNode(self.ParentID)

    @property
    def Root(self):
        return glb.pnodes.GetPNode(self.RootID)

    @property
    def BuildTargets(self):
        try:
            return self.__build_targets
        except AttributeError:
            return None

    @BuildTargets.setter
    def BuildTargets(self, value):
        if not value:
            try:
                del self.__build_targets
            except AttributeError:
                pass
            return
        self.__build_targets = value

# vim: set et ts=4 sw=4 ai ft=python :

