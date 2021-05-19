
import copy
import enum
import hashlib
import os
import pprint
import sys
import time
import traceback
import types
from builtins import zip
from typing import Optional

import parts.core.builders as builders
import parts.core.util as util
import parts.pnode.part_info as part_info
import parts.pnode.pnode as pnode
import parts.pnode.pnode_manager as pnode_manager
import parts.pnode.section as section
import SCons.Node
from parts.core.states import FileStyle, LoadState

# these imports add stuff we will need to export to the parts file.
#from .. import requirement
from .. import (api, common, datacache, dependson, errors, functors, glb,
                node_helpers, packaging, part_logger, platform_info, settings,
                version)
from ..core import util
from ..target_type import target_type


def safe_visited_call(node):
    '''
    In SCons 2.3.1 they changed node.visited() method implementation
    to reference node.executor attribute which is missed for source nodes.
    To safely call the method we temporary create an executor for the node
    and then reset it.
    '''
    try:
        node.visited()
    except AttributeError:
        node.get_executor()
        try:
            node.visited()
        finally:
            node.reset_executor()


class Part(pnode.PNode):
    """description of class"""

    __slots__ = [
        # calling params
        '__append',     # This is stuff we want to append to the environment
        '__prepend',    # this is stuff we would want to prepend
        '__kw',         # this is stuff we want to replace

        # Debug stack for where this part was called
        '__stackframe',

        # basic attributes
        '__ID',
        '__file',           # the Parts file
        '__part_dir',       # The path of the part file.
        '__src_dir',        # the path used to find sources from
        '__version',        # the version of this part
        '__name',           # the name of this part (foo.bar.goo)
        '__alias',          # the alias of this part (foo0.bar0.goo0)
        '__short_name',     # the short name of this parts (goo)
        '__short_alias',    # the short name of this parts (goo0)
        '__parent',         # the parent part object, else None
        '__root',           # the root part object, might be self
        '__subparts',       # dictionary of sub-parts

        '__mode',           # special build values
        '__uses',           # list of Parts that this we want to map to first
        '__settings',       # The setting object used to create the environment
        '__env',            # the prime SCons Environment
        '__platform_match',  # this is how we can depend on this object
        '__config_match',

        '__env_diff',  # the difference of this environment with the Default environment of the defining Setting object
        '__env_diff_sig',  # The MD5 value of this difference
        '__env_mini_diff_sig',  # a short form of it

        '__build_context_files',
        '__config_context_files',

        '__sections',  # the section the part contains
        '__classic_section',  # the classic format case


        # sdk data
        '__create_sdk',     # create the SDK
        '__create_sdk_data',  # This is the data for the SDK file we will want to make
        '__sdk_files',      # the file that are copied in to the SDK
        '__sdk_file',       # the name of the SDK file we will make.. if any

        # some state stuff
        '__force_load',  # tells us that this Parts should be loaded
        '__format',  # The format of the part file
        '__is_setup',    # the Parts has been setup to be buildable
        '__is_default_target',  # do we set this as a default build target
        '__defining_section',  # current section we are defining
        '__read_state',

        # packaging stuff
        '__package_group',  # the package group this maps to

        # SCM stuff
        '__scm',  # The information on how to check out this Part, None to use as file as local path.
        '__extern_scm',  # this is for out or repo build files based builds

        # compatibility stuff
        '__sdk_or_installed_called',  # this is to help with issues with unit tests sub parts in classic format
        '__order_value',  # use to help with ordering in a compatible way between classic and new formats
        '__cache',  # used for internal caching of data
        '__build_targets',  # How does it care about SCons.Script.BUILD_TARGETS
        # '__dict__'
    ]
    # constructor
    def __init__(self, file=None, mode=[], scm_t=None, default=False,
                 append={}, prepend={}, create_sdk=True, package_group=None, alias=None, name=None,
                 Settings=None, extern=None,
                 **kw):

        self.__ID = kw.pop('ID', None)
        # stuff for creating an environment
        # need to store this so we can pass to an sub-part
        self.__append = append  # This is stuff we want to append to the environment
        self.__prepend = prepend  # this is stuff we would want to prepend
        self.__kw = kw  # this is stuff we want to replace
        self.__mode = common.make_list(mode)
        self.__settings = Settings
        # version number.. ideally this maps to root version only
        # but in some cases we need it in Parts that are not fully defined yet
        self.__version = version.version(kw.get('version', '0.0.0'))
        # sdk stuff
        # do we want to create the sdk or skip it
        self.__create_sdk = create_sdk
        # This is the data for the SDK file we will want to make
        self.__create_sdk_data = []
        # the file that are copied in to the SDK
        self.__sdk_files = []
        # the name of the SDK file we will make.. if any
        self.__sdk_file = None

        self.__env_diff = None
        # packaging stuff
        # what package group to add this to
        if package_group:
            self.__package_group = package_group
        else:
            self.__package_group = None
        # state stuff
        self.__is_default_target = default  # do we set this as a default build target

        # the part has been fully processed or not
        # self.__Processed=False

        # this is the style/format the part file used
        self.__format = FileStyle.UNKNOWN

        # everything we depend on, implicit and explicit,
        # contain component objects.. change to part and component mix latter??
#        self.__full_dependson=[]
#        self.__dependson=[] # has to be a list as the order matters for linking
        # these are Parts that this Part uses, but may not depend on.
        # we will make sure these are processed before this Part is processed
        # used primarily for classic formats
        # otherwise the Depends on logic will try to verify these object for possible
        # matches, else error. ie IF the part name matches the rest of it has to
        # depend ons statements with no matching name fall through the "global"
        # set of Parts to match
        # ideally stored only on root_parts
        if self.__kw.get('parent_part', None) is None:
            self.__uses = common.make_list(kw.get("requires", []))

        # data we will cache later
        self.__cache = {}
        # the sections that are defined in a Part
        self.__sections = {}
        # the environment object for the Part
        self.__env = None

        # basic data
        # the alias.. such as
        self.__alias = alias
        self.__short_alias = alias
        # The part name.. parent.name+.+short_name
        self.__name:Optional[str] = name
        # the short name.. or exact value given to this part as the name
        self.__short_name:Optional[str] = name
        # the parent part object
        # check for kw for parent_part key
        self.__parent = self.__kw.pop('parent_part', None)
        # the top level part object
        self.__root = None
        # any subparts to this Part
        self.__subparts = {}

        self.__defining_section = None
        self.__classic_section = None

        # collection of data we make during the build

        # files that effect the possible good state of this build context
        # of anything this Part might fix
        self.__build_context_files = set()
        self.__config_context_files = {}

        # how we can get the source, None is local
        self.__scm = scm_t
        # extern mapping if any
        self.__extern_scm = extern

        # the file for this part, if any
        self.__file = str(file)
        # the part_dir we need to make sure SCons as no issues when loading the Part file
        self.__part_dir = None
        self.__src_dir = None
        # this is how we can depend on this object
        self.__platform_match = None
        self.__is_setup = False

        # use to help with ordering in a compatible way between classic and new formats
        self.__order_value = 0

        # this is to help with issues with unit tests sub parts in classic format
        self.__sdk_or_installed_called = False

        # this to force loading .. bypassing caching features
        self.__force_load = kw.get('force_load', False)

        # this is for reporting better error messages
        self.__stackframe = errors.GetPartStackFrameInfo()

        # some state stuff
        try:
            self.__read_state = self.__read_state
        except Exception:
            self.__read_state = LoadState.NONE
        super(Part, self).__init__()

    @staticmethod
    def _process_arg(**kw):
        id = kw.get('ID')
        if id:
            setup = False
        else:
            setup = True
        return id, setup

    # properties
    # calling params

    @property
    def _append(self):
        return self.__append

    @property
    def _prepend(self):
        return self.__prepend

    @property
    def _kw(self):
        return self.__kw

    # basic attributes
    @property  # readonly non-mutable
    def File(self):
        return self.__file

    @property  # readonly non-mutable # compat
    def SourcePath(self):
        return self.__src_dir

    @property  # readonly non-mutable
    def SourceDir(self):
        """
        Get the directory that is used for refer to the sources refereed to in the Part file.
        """
        return self.__src_dir

    @property  # readonly non-mutable
    def PartsDir(self):
        """Get the current Directory where the part file exits."""
        return self.__part_dir

    @property
    def Version(self) -> version.version:  # mutable
        """Get the current version."""
        if self.isRoot:
            return self.__version
        return self.__root.Version

    @Version.setter
    def Version(self, version: version.version) -> None:
        if self.isRoot:
            self.__version = version
        else:
            self.__root.Version = version

    # compatibility
    version = Version

    @property  # readonly as it based on full version
    def ShortVersion(self) -> str:
        """Get the current short version."""
        return self.__root.__version[0:2]

    @property  # readonly non-mutable
    def Alias(self):
        """Get the current alias."""
        if self.__alias is None:
            self.__alias = self.__ID
        return self.__alias
    alias = Alias

    @property
    def ID(self):
        if self.__ID is None:
            self.__ID = self.__alias
        return self.__ID

    @property  # readonly non-mutable
    def ShortAlias(self):
        """Get the current alias."""
        return self.__short_alias

    @property
    def Name(self) -> str:  # read only non-mutable as it based on short name and parent
        """Get the current parent Part name."""
        if self.__name is None:
            self.ShortName = self.__short_alias
        return self.__name

    @property  # readonly
    def ShortName(self) -> str:
        """Get the current parent Part name."""
        if self.__short_name is None:
            self.ShortName = self.__short_alias
        return self.__short_name

    @ShortName.setter
    def ShortName(self, val: str) -> None:
        self._set_name(val)

    # For backward compatibility
    def _set_name(self, name, force_parent=None):
        oldname = self.__name
        if force_parent is not None:
            self.__name = f"{force_parent}.{name}"
        elif self.__parent is not None:
            self.__name = f"{self.Parent.Name}.{name}"
        elif self.__parent is None:
            self.__name = name
        self.__short_name = name
        if oldname != self.__name and oldname:
            api.output.warning_msg("Name changed: {0} to {1}".format(oldname, self.__name))
            glb.engine._part_manager.add_name_alias(self.__name, self.__alias, oldname)
        else:
            glb.engine._part_manager.add_name_alias(self.__name, self.__alias)

    @property  # readonly mutable
    def Parent(self) -> Optional['Part']:
        """Get the current parent Part, or None if there is no parent"""
        return self.__parent

    @property  # readonly mutable
    def Root(self) -> 'Part':
        """Get the current root Part."""
        return self.__root

    @property  # readonly non-mutable #remove?
    def ParentName(self) -> Optional[str]:
        """Get the current parent Part name."""
        if self.__parent is None:
            return None
        return self.__parent.Name

    @property  # readonly non-mutable #remove?
    def RootName(self) -> str:
        """Get the current root Part name."""
        return self.__root.Name

    @property  # readonly non-mutable
    def SubParts(self):
        return list(self.__subparts.values())

    @SubParts.setter
    def SubParts(self, obj):
        try:
            if id(obj) != id(self.__subparts[obj.ID]):
                api.output.error_msg("%s is already defined" % obj.Alias)
        except KeyError:
            self.__subparts[obj.ID] = obj

    @property
    def Mode(self):  # readonly non-mutable
        return self.__mode  # may want to return a copy

    @property  # readonly non-mutable
    def Uses(self):
        if self.isRoot:
            try:
                return self.__cache['uses']
            except KeyError:
                tmp = []
                for p in self.__uses:
                    if util.isString(p):
                        # assume this is an Alias
                        tmp_alias = p
                        p = glb.engine._part_manager._from_alias(p)
                        if p is None:
                            api.output.error_msg('Cannot use non existing Part "%s"' % tmp_alias)
                    elif isinstance(p, Part):
                        # just a Validation check
                        pass
                    else:
                        api.output.error_msg('Invalid type for a Part to dependon "%s"' % (type(p)))
                    tmp.append(p)
                self.__cache['uses'] = tmp
            return self.__cache['uses']
        else:
            return self.__root.Uses

    def usesPart(self, obj):
        ''' return True if the part passed in is used by this parts'''
        if self.isRoot:
            # need to test that this works as expected
            return obj in self.Uses
        return self.__root.usesPart(obj)

    @property
    def Settings(self):  # readonly mutable
        return self.__settings

    @property
    def Env(self):
        """get the default environment used with this Part"""
        return self.__env

    @property
    def PlatformMatch(self):  # readonly
        ''' Returns the SystemPlatform this part will match on for dependencies
        '''
        return self.__platform_match

    @property
    def ConfigMatch(self):  # readonly
        ''' Returns the SystemPlatform this part will match on for dependencies
        '''
        return self.__config_match

    @property
    def _env_diff(self):  # readonly
        return self.__env_diff

    @property
    def _env_diff_sig(self):  # readonly
        return self.__env_diff

    @property
    def _build_context_files(self):
        '''

        '''
        if self.isRoot:
            return self.__build_context_files
        else:
            return self.__root._build_context_files

    @property
    def _config_context_files(self):
        '''

        '''
        if self.isRoot:
            return self.__config_context_files
        else:
            return self.__root._config_context_files

    # sdk stuff (finish SDK stuff)
    @property
    def SdkFile(self):
        return self.__sdk_file

    @property
    def _sdk_files(self):
        return self.__sdk_files

    @property
    def _create_sdk_data(self):
        return self.__create_sdk_data

    @property
    def CreateSdk(self):
        return self.__create_sdk

    # State
    @property
    def ForceLoad(self):
        return self.__force_load

    @property
    def Format(self) -> FileStyle:
        return self.__format

    @Format.setter
    def Format(self, style: FileStyle):
        '''
        currently set to new or classic.. need to clean up latter to something better
        '''
        self.__format = style

    @property
    def isClassicFormat(self):
        return self.__format == FileStyle.CLASSIC or self.__format == FileStyle.UNKNOWN

    @property
    def isRoot(self):
        return self.__alias == self.__root.Alias

    @property
    def isSetup(self):
        '''returns if we have setup the environment for basic usage'''
        return self.__is_setup

    @property
    def isDefaultTarget(self):
        '''Returns true is this Part is set as a default Target to be built'''
        return self.__is_default_target

    @property
    def isVisited(self) -> bool:
        return self.LoadState == LoadState.FILE

    # packaging stuff
    @property
    def PackageGroup(self):
        '''the Package group this Part is mapped to'''
        return self.__package_group

    # scm stuff
    @property
    def Scm(self):
        """return the Scm object"""
        return self.__scm

    @property
    def ExternScm(self):
        return self.__extern_scm

    # some compatibility stuff
    @property
    def _sdk_or_installed_called(self):
        return self.__sdk_or_installed_called

    @_sdk_or_installed_called.setter
    def _sdk_or_installed_called(self, value):
        self.__sdk_or_installed_called = value

    @property
    def _order_value(self):
        return self.__order_value

    @_order_value.setter
    def _order_value(self, x):
        self.__order_value = x

    @property
    def _cache(self):
        return self.__cache

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

    # section forwarding API
    # given that we can only define one section at a time
    # may tweak when we get new formats working again
    @property
    def DefiningSection(self):
        if self.__defining_section:
            return self.__defining_section

        return self.__classic_section

    @DefiningSection.setter
    def DefiningSection(self, sec):
        self.__defining_section = sec

    def Section(self, case):
        return self.__sections[case]

    @property
    def Sections(self):
        return self.__sections

    # hack till we get new format stuff working...

    def _AddSection(self, name, obj):
        self.__sections[name] = obj

    # re look at this function when we add new format
    def _hasTargetFiles(self) -> bool:
        return bool(self.__classic_section.Targets)

    # see if we can remove the env arg latter
    def _setup_(self, _env=None, *lst, **kw):

        # if this is a help mode run ( get help setting for user)
        # we want to skip this work
        if glb.engine._build_mode == 'help':
            return

        # this value allows us a work around to the
        # issue of generating an ID vs a full setup
        genid = kw.get('gen_ID')

        # is this core like the iapat object?

        if _env is None:
            # if none have been setup, use the default Settings object
            if self.__settings is None:
                self.__settings = settings.DefaultSettings()

            self.__env = self.__settings.Environment(
                prepend=self.__prepend.copy(),
                append=self.__append.copy(),
                **self.__kw.copy()
            )

        else:
            self.__env = _env

        if self.__env_diff is None:
            # basic data
            # create diff with default environment
            base_env = self.__settings._env_const_ref()
            # check to see if the big three are different config, target_platform, toolchain
            # if so we want to diff off of that case, as these items can make a massive set
            # of changes we really want to ignore, or don't care about as much as the
            # one item that caused them to change
            diff = {}
            if self.__mode != []:
                diff = {'mode': self.__mode}
            if base_env['TARGET_PLATFORM'] != self.__env['TARGET_PLATFORM'] or\
                    base_env.subst('$CONFIG') != self.__env.subst('$CONFIG') or\
                    base_env['toolchain'] != self.__env['toolchain']:
                if base_env['TARGET_PLATFORM'] != self.__env['TARGET_PLATFORM']:
                    diff['TARGET_PLATFORM'] = self.__env['TARGET_PLATFORM']
                if base_env['toolchain'] != self.__env['toolchain']:
                    diff['toolchain'] = self.__env['toolchain']
                if base_env.subst('$CONFIG') != self.__env.subst('$CONFIG'):
                    diff['CONFIG'] = self.__env.subst('$CONFIG')
                base_env = self.__settings._env_const_ref(
                    TARGET_PLATFORM=self.__env['TARGET_PLATFORM'],
                    CONFIG=self.__env.subst('$CONFIG'),
                    toolchain=self.__env['TOOLCHAIN']
                )

            diff.update(diff_env(base_env, self.__env, ['requires']))

            if diff != {}:

                md5 = hashlib.md5()
                md5.update(common.get_content(diff))
                self.__env_diff = diff
                self.__env_diff_sig = md5.hexdigest()
                self.__env_mini_diff_sig = self.__env_diff_sig[-4:]
                path_sig = self.__env_mini_diff_sig
            else:
                self.__env_diff = {}
                self.__env_diff_sig = ''
                self.__env_mini_diff_sig = ''
                # since we we can load the same part from different directories, we assume a version difference
                # we don't know what the difference is yet (as the part file is not read). We md5 the path to make a difference
                # if there is no version difference, we will get an ambiguous error message later when we try to build,
                # via same outputs, or via mapper function not having more than one match.
                md5 = hashlib.md5()

                md5.update(self.__env.subst(self.__file).encode())
                md5.update(self.__env_diff_sig.encode())
                path_sig = md5.hexdigest()[-4:]

        # We need to set to the alias value as this is the unique ID used to map data internally
        if self.__alias is None:
            # we don't have a user provided alias.. make it off the file name
            tmp = self.__env.subst(self.__file)

            tmp = os.path.splitext(os.path.split(tmp)[1])[0]  # we only want the file name
            # path sig would be enough, but the alias in some form gives the user a value
            # they can reconize.
            tmp = "{0}-{1}".format(tmp, path_sig)
            self.__alias = tmp
            self.__short_alias = tmp
            self.__short_name = tmp
        # we need to check if this is a sub Parts

        if self.__parent is None:
            # this is the parent so we apply the global Prefix add Postfix values
            self.__alias = self.__env.subst('${ALIAS_PREFIX}%s${ALIAS_POSTFIX}' % self.__short_alias)
            self.__root = self
            self.__version = version.version('0.0.0')
        else:
            # we have a parent
            self.__alias = self.__parent.Alias + '.' + self.__short_alias
            self.__root = self.__parent.Root
            if not genid:
                self.__parent.SubParts = self
        if genid:
            return
        # resolve the File name for the Part we will load latter
        self.__make_part_env()
        if self.__parent is None:
            dir_tmp = self.__env.Dir('#')
        else:
            dir_tmp = self.__env.Dir(self.__parent.PartsDir)

        # setup scm object. We always have one. null_t is the default
        if self.__extern_scm:
            self.__extern_scm._setup_(self)
        self.__scm._setup_(self)  # update env with scm level defines

        if self.isRoot and self.ExternScm:
            # set up the extern scm
            self.__file = dir_tmp.File(self.__extern_scm.PartFileName)

        elif self.isRoot:
            self.__file = dir_tmp.File(self.__scm.PartFileName)
        else:
            self.__file = dir_tmp.File(self.__env.subst(self.__file))  # the Parts file to read in

        # the src_path we need to make sure SCons as no issues when loading the Part file
        self.__part_dir = self.__file.srcnode().Dir(".")

        # Some location information
        # the part file as a node
        self.__env['PART_FILE'] = self.__file
        # the directory of the part file
        self.__env['PART_DIR'] = self.__part_dir

        #print(self.__root.Scm.CheckOutDir.abspath, self.__file.abspath, self.__file.is_under(self.__root.Scm.CheckOutDir), self.__root.Scm.CheckOutDir.is_under(self.__file))
        if self.__file.is_under(self.__root.Scm.CheckOutDir):
            self.__src_dir = self.__part_dir
        else:
            # this is an extern part file build. In this case the source directory is the checkout directory
            # this could be changes if we defined some sub_dir to start as the source.. but that opens up other
            # issues I don't want to deal with.. so keep it simple on our end for the moment
            self.__src_dir = self.__root.Scm.CheckOutDir
        self.__env['SRC_DIR'] = self.__src_dir

        # add information on how to map this Parts
        # allow us to make a part platform independent in some way
        self.__platform_match = copy.copy(self.__env['TARGET_PLATFORM'])
        if self.__kw.get('platform_independent', self.__kw.get('platform_indepenent', False)):
            self.__platform_match = platform_info.SystemPlatform('any', 'any')
            if self.__kw.get('platform_indepenent'):
                api.output.warning_msg('use of "platform_indepenent" is depreciated. Please use "platform_independent" instead.')
        if self.__kw.get('os_independent', self.__kw.get('os_indepenent', False)):
            self.__platform_match.OS = 'any'
            if self.__kw.get('os_indepenent'):
                api.output.warning_msg('use of "os_indepenent" is depreciated. Please use "os_independent" instead.')
        if self.__kw.get('architecture_independent', self.__kw.get('architecture_indepenent', False)):
            self.__platform_match.ARCH = 'any'
            if self.__kw.get('architecture_indepenent'):
                api.output.warning_msg(
                    'use of "architecture_indepenent" is depreciated. Please use "architecture_independent" instead.')

        self.__config_match = not self.__kw.get('config_independent', False)

        #self.__classic_section = glb.pnodes.Create(section.build_section, self)
        self.__is_setup = True

    def _merge(self, otherobj):
        # turn other object in to this guy the best we can
        otherobj.__dict__ = self.__dict__

    def __make_part_env(self):

        # set alias

        self.__env['ALIAS'] = self.__alias
        self.__env['PART_ALIAS'] = self.__alias
        # The Alias Parent
        # part_info['PARENT_ALIAS']=parent_alias

        # The Alias Short Form
        self.__env['SHORT_ALIAS'] = self.__short_alias

        # logger and task spawners
        self.__env['SPAWN'] = '${PART_SPAWNER(__env__)}'

        # package logic ( as it is currently)
        self.__env['PARTS_PACKAGE_GROUPS'] = self.__package_group
        if self.__package_group is not None:
            packaging.PackageGroup(self.__package_group, self.__alias)

        # Setup the Environment BUILD_DIR in the LIBPATH
        # might need more.. to add as needed
        libpath = ['$BUILD_DIR']
        self.__env.Append(LIBPATH=libpath)

        # setup the mode
        if not self.__mode:
            self.__mode.append("default")
        # add any global mode values to known set
        for m in self.__env['mode']:
            if m == "default":
                pass
            elif m in self.__mode:
                # if self.isRoot:
                # api.output.warning_msgf(
                #'Mode value "{val}" was defined globally and locally. This may cause ambiguous dependency matching',
                # val=m,
                # id=self.ID
                # )
                pass
            else:
                self.__mode.append(m)
        self.__env['MODE'] = self.__mode

        # alias info
        self.__env['PART_ROOT_ALIAS'] = self.__root.Alias
        if self.__parent:
            self.__env['PART_PARENT_ALIAS'] = self.__parent.Alias
        else:
            self.__env['PART_PARENT_ALIAS'] = None

        # name info
        self.__env['PART_NAME'] = "${PARTNAME('" + self.__alias + "')}"
        self.__env['PART_SHORT_NAME'] = "${PARTSHORTNAME('" + self.__alias + "')}"
        self.__env['PART_ROOT_NAME'] = "${PARTS('" + self.__root.__alias + "','Name')}"
        self.__env['PART_ROOT_SIG'] = self.__root.__env_diff_sig
        self.__env['PART_ROOT_MINI_SIG'] = self.__root.__env_mini_diff_sig
        self.__env['PART_MINI_SIG'] = self.__env_mini_diff_sig
        if self.__parent is None:
            self.__env['PART_PARENT_NAME'] = None
        else:
            self.__env['PART_PARENT_NAME'] = "${PARTS('" + self.__parent.__alias + "','Name')}"

        # version info
        self.__env['PartVersion'] = self.__env.PartVersion
        self.__env['PART_VERSION'] = "${PartVersion()}"
        self.__env['PART_SHORT_VERSION'] = "${PartVersion()[0:2]}"
        self.__env['PART_MAJOR_VERSION'] = "${PartVersion()[0]}"
        self.__env['PART_MINOR_VERSION'] = "${PartVersion()[1]}"

        if "__DEBUG__POBJ__" in self.__env["MODE"]:
            self.__env['POBJ'] = self

    # def __str__(self):
        #pp = pprint.PrettyPrinter(indent=4)
        # return pp.pformat(self.__dict__)

    def _setup_sdk(self):
        '''
        This function tried setting up the old generate a SDK part logic
        '''
        # do nothing at this time....
        return
        create_sdk = True
        if (self.__env['CREATE_SDK'] == False and self.__create_sdk == True):
            create_sdk = False

        if create_sdk == True:
            # set up the builder for the SDK file
            v = self.__env.__CreateSDKBuilder__([], self.__file)
            self.__sdk_file = v[0]
            # self.__env.Alias('${PART_SDK_CONCEPT}${PART_ALIAS_CONCEPT}'+self.__alias,v)
            self.__env.Alias('${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}' + self.__alias, v)

            if self.__parent is not None:
                sdkname = "%s_%s.sdk.parts" % (self.__name, self.Version)
                args = {
                    'alias': self.__short_alias,
                    'parts_file': sdkname,
                    'mode': self.__mode,
                    'scm_type': None,
                    'default': self.__set_as_default_target,
                    'append': self.__append,
                    'prepend': self.__prepend,
                    'create_sdk': False}
                self.__parent._create_sdk_data.append(('Part', [common.named_parms(args),
                                                                common.named_parms(self.__kw)]))

    def _map_targets(self):
        '''
        Here we map all known target files that happen in this component
        to the alias value, to ensure that it is built in case there are actions
        that are no mapped correctly to some action that is mapped to the alias
        such as and sdk or install action
        '''
        self.__classic_section._map_targets()
        return

    class build_target_wrapper:
        '''
        There are some .parts files that inspect SCons.Script.BUILD_TARGETS
        value to decide whether to build unit-tests or not. We need to determine
        such parts to make sure they are loaded from file and not from cache
        when BUILD_TARGETS contain targets from different sections.
        Wrapping SCons.Script.BUILD_TARGETS. Need to wrap reading methods:
        __getitem__
        __iter__
        __contains__
        __getslice__
        See http://docs.python.org/2/reference/datamodel.html#emulating-container-types
        and http://docs.python.org/2/reference/datamodel.html#additional-methods-for-emulation-of-sequence-types
        for reference
        '''
        __slots__ = ['__obj', '__accessed']

        def __init__(self, obj):
            self.__obj = obj

        @property
        def obj(self):
            '''
            Read-only property. Returns the wrapped object.
            '''
            return self.__obj

        @property
        def accessed(self):
            '''
            Returns C{True} if the wrapped object is accessed for reading.
            '''
            try:
                return self.__accessed
            except AttributeError:
                return False

        def __getattr__(self, name):
            '''
            Wraps the object's method to register reading access.
            '''
            return getattr(self.__obj, name)

        # We override read-access methods. To avoid cut/pasting we define them dynamically.
        def def_method(name):
            def method(self, *args, **kw):
                result = getattr(self.obj, name)(*args, **kw)
                self.__accessed = True
                api.output.warning_msg(
                    "Inspecting internal SCons.Script.BUILD_TARGETS variable "
                    "is a bad coding pattern. Consider re-factoring to avoid that.")
                return result
            return method
        for name in ('__iter__', '__getitem__', '__getslice__', '__contains__'):
            locals()[name] = def_method(name)
        del name
        del def_method

    class part_loading_context:
        '''
        Class used as .parts file loading context. It solves two tasks:
         1. Filters out exceptions raised during the file reading.
         2. Registers access to SCons.Script.BUILD_TARGETS list by .parts file.
        '''

        def __init__(self, part_file, keep_going):
            '''
            @param[in] self - part_loading_context instance
            @param[in] part_file - C{SCons.Node.Node} instance representing .parts file.
            @param[in] keep_going - Flag to decide if we need to continue loading in
                       case of exception raised.
            '''
            if keep_going:
                self.__exit__ = self.__keep_going
            self.part_file = part_file

        def __enter__(self):
            '''
            Enter the context.
            '''
            SCons.Script.BUILD_TARGETS = Part.build_target_wrapper(
                SCons.Script.BUILD_TARGETS)
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            '''
            Exit the context.
            '''
            # Do not suppress any exceptions
            self.build_targets_accessed = SCons.Script.BUILD_TARGETS.accessed
            SCons.Script.BUILD_TARGETS = SCons.Script.BUILD_TARGETS.obj
            return None

        def __keep_going(self, exc_type, exc_value, tb):
            '''
            This method is called on exit when the context object has been constructed
            with keep_going parameter set to True.
            '''
            type(self).__exit__(self, exc_type, exc_value, tb)
            # Suppress all but LoadStoredError exceptions
            if exc_type == errors.LoadStoredError:
                return None  # Do not suppress this exception
            api.output.warning_msg(
                "Exception thrown while processing {0}\n{1}".format(
                    self.part_file.srcnode().abspath, traceback.format_exc()))
            api.output.print_msg("Will try to continue...")
            return True

    def ReadFile(self):
        # we process the file
        # and check at the end if we processed a new format or an old format
        # error on mixed formats??

        if self.LoadState == LoadState.FILE:
            print("\033[1;32m %s was already read" % self.__alias)
            return

        if self.LoadState < LoadState.FILE:
            # sort of ugly.. but SCon was to aggressive here in storing state
            try:
                del self.__file._memo['stat']
            except KeyError:
                pass

            # setup what we want to export to the part file
            # global objects
            export_map = glb.parts_objs

            # add the sections
            # we do this when we read as there might have been new sections dynamically added
            sections_proxies = {}
            for name, definition in glb.section_definitions.items():
                proxy = definition.CreateProxy(env=self.Env)
                sections_proxies[definition.Name] = proxy
                if definition.Name == "build":
                    # pre-create a build/default Section object
                    # needed for backwards compatibility.
                    self.__sections[definition.Name] = self.__classic_section = glb.pnodes.Create(
                        section.Section, proxy=proxy, pobj=self,)
                if definition.Name == "unit_test":
                    # pre-create a build/default Section object
                    # needed for backwards compatibility.
                    unit_test = glb.pnodes.Create(section.Section, proxy=proxy, pobj=self, register_node=False)
                    unit_test_proxy = proxy

                    # this is a hack to allow unit test to work..  We store the proxies in a cache
                    self.__cache['unit_test'] = proxy, unit_test

            # define the sections for this part
            export_map.update(sections_proxies)
            # the default environment
            env = self.__classic_section.Env

            # this is compatibility to parts that depend on
            # passing DependOn requirements with internal=False
            # this was change in 0.16 to be True by default
            if env.get("COMPAT_REQ_INTERNAL"):
                api.output.warning_msg(f"Part {self.Root.Alias} is set to use deprecated default value of internal=False in DependsOn.",show_stack=False,print_once=True)
                glb.compat_internal+=1


            # global object that need to be mapped
            for k, v in glb.parts_objs_env.items():
                export_map[k] = v(env)

            # add the environment
            export_map['env'] = env
            env._log_keys = True  # this allow us to set what is different in the environment

            # ####################################
            # this is to setup variant directories

            # this is the primary build directory
            bdir = env.Dir(env.subst('$BUILD_DIR'))
            env['BUILD_DIR_NODE'] = bdir
            # this is the directory that contains the Parts file
            part_dir = self.__part_dir
            # this is the directory we are using as the root to reffer to nodes
            src_dir = self.__src_dir

            bk_path = sys.path
            sys.path = [src_dir.abspath] + bk_path
            # variant dir for file out of parts tree but under Sconstruct
            env.VariantDir(env.Dir('$OUTOFTREE_BUILD_DIR'), "#", self.__env['duplicate_build'])
            # variant dir for file out of Sconstruct tree but under the root
            # this does not cover windows drives that are different from the current drive c:\
            env.VariantDir(env.Dir('$ROOT_BUILD_DIR'), "/", self.__env['duplicate_build'])
            if part_dir != src_dir:
                # source path and parts directory are different
                # we are out of repo or extern case. For this we need to make a mapping
                # to allow access to node in the part directory
                # this should allow the ability to refer to node in "extern" area via saying
                # $PART_DIR/<some file> and have it build correctly out of source
                env['PART_DIR'] = env.Dir('$BUILD_DIR/_extern')
                env.VariantDir(env.Dir('$BUILD_DIR/_extern'), self.__part_dir, self.__env['duplicate_build'])

            st = time.time()
            if (glb.engine._build_mode == 'build') or (os.path.exists(self.__file.srcnode().abspath) == True):
                if os.path.exists(self.__file.srcnode().abspath) == False:
                    api.output.error_msg('Parts file ' + self.__file.srcnode().abspath +
                                         " was not found.", stackframe=self.__stackframe)

                ######################################
                # Call the part file
                with self.part_loading_context(self.__file, SCons.Script.GetOption('keep_going')) as context:
                    errors.ResetPartStackFrameInfo()
                    self.__env.SConscript(
                        self.__file,
                        src_dir=src_dir,
                        variant_dir=bdir,
                        duplicate=self.__env['duplicate_build'],
                        exports=export_map
                    )
                # a check on context to see if stuff went wrong or was messed with
                if context.build_targets_accessed:
                    # Remember the BUILD_TARGETS state
                    self.BuildTargets = set(
                        target_type(target).Section for target in
                        SCons.Script.BUILD_TARGETS)

            api.output.verbose_msg(['part_read'], 'Parts file {0} read time: {1}'.format(
                self.__file.srcnode().abspath, time.time() - st))

            # check the sections to see if we have valid sections and if so they get added to the __section variable
            for name, proxysec in sections_proxies.items():
                # get the definition
                definition = glb.section_definitions[name]
                # the sections had something defined
                # we will validate all the phases at different point
                sec = None
                if name == "build":
                    # Should be added already
                    pass
                elif name == "unit_test" and definition.isDefined(proxysec):
                    # this is special case for compatibility.
                    # might be added already if in compatibility case
                    # however it would not be registered yet
                    sec = unit_test
                    glb.pnodes.AddPNodeToKnown(sec)
                elif definition.isDefined(proxysec):
                    # make a new section
                    sec = glb.pnodes.Create(section.Section, proxy=proxysec, pobj=self,)
                if sec:
                    self.__sections[name] = sec

            # clean up cache key that we don't need anymore
            del self.__cache['unit_test']

            # we tag the Directory nodes so we can latter sort unknown items faster, by checking the directory ownership
            env._log_keys = False

            # set file as read
            # todo .. need to relook at the need for this!
            self.__classic_section.LoadState = LoadState.FILE

            # hack to help with compatibility issues as we fixed up the mapping table.
            if self.__classic_section.Env.get('PART_REVERSE_EXPORTS_LIBS') == True:
                try:
                    self.__classic_section.Exports['LIBS'][0].reverse()
                except KeyError:
                    pass

            if env.get("COMPAT_REQ_INTERNAL"):
                glb.compat_internal-=1

            sys.path = bk_path

    # sections based API's
    def _has_section_defined(self, name):
        '''
        tests to see if a certain section is defined
        return None if the file has not been read (ie this is unknown)
        otherwise it returns True or False
        '''
        if self.LoadState == LoadState.NONE:
            return name in self.__sections
        return None

    def _has_section_phase_been_called(self, section, phase):
        '''
        Tells us if this section and phase has been called already
        Returns True or False

        This allow the processfunc of a section to see if it needs to call this
        section phase or not to prevent wasted time in processing known items
        '''
        try:
            if self.__cache["%s%scalled" % (section, phase)]:
                return True
        except KeyError:
            return False

    def _call_section(self, section, phase):
        '''
        Call the section function defined for a given phase.
        This will cache the fact that it was called, so it get called only once
        It will throw an error if there is no such combination defined
        '''
        try:
            if self.__cache[f"{section}{phase}called"]:
                return
        except KeyError:
            tmp = self.__env.fs.getcwd()
            try:
                self.__env.fs.chdir(self.__env.Dir(self.__env.subst("$BUILD_DIR")), True)
            except OSError:
                self.__env.fs.chdir(self.__env.Dir(self.__env.subst("$BUILD_DIR")))
                os.chdir(self.__env.Dir(self.__env.subst("$BUILD_DIR")).srcnode().abspath)

            lst = getattr(self.__sections[section], 'func_' + phase)
            if lst == []:
                api.output.warning_msg("No phase function callbacks for %s.%s in Part %s" % (section, phase, self.__name))
            for i in lst:
                i(self.__env)

            self.__env.fs.chdir(tmp, True)
            self.__cache[f"{section}{phase}called"] = True

    def hasFileChanged(self):
        '''
        Has the file changed in some way.

        The is considered changed if it was modified or the parent was modify.
        '''
        try:
            return self.__cache['hasFileChanged']
        except KeyError:
            data = self.Stored
            # check that stored data exists
            if data is None:
                self.__cache['hasFileChanged'] = True
                self.UpdateReadState(LoadState.FILE)
                return True
            # Get File Node
            tmp = glb.pnodes.GetNode(data.File['name'], SCons.Node.FS.File)
            if tmp is None:
                self.__cache['hasFileChanged'] = True
                self.UpdateReadState(LoadState.FILE)
                return True
            # does this node look different
            if tmp.changed_since_last_build(tmp, tmp.make_ninfo_from_dict(data.File)):
                self.__cache['hasFileChanged'] = True
                self.UpdateReadState(LoadState.FILE)
                return True
            # does the parent look different
            try:
                if not data.Parent.isFileUpToDate():
                    self.__cache['hasFileChanged'] = True
                    self.UpdateReadState(LoadState.FILE)
                    return True
            except AttributeError:
                pass
            self.__cache['hasFileChanged'] = False
            return False

    def UpdateReadState(self, state):
        if self.__read_state < state:
            self.__read_state = state

    @property
    def ReadState(self):
        substate = self.SubPartReadState
        self.UpdateReadState(substate)
        return self.__read_state

    @property
    def SubPartReadState(self) -> LoadState:
        # check that stored data is exits
        data = self.Stored
        if data is None:
            return LoadState.FILE
        state = LoadState.NONE
        for name in data.SubPartIDs:
            sub = glb.pnodes.GetPNode(name)
            if sub:
                if sub.ReadState > state:
                    state = sub.ReadState
                if state >= LoadState.FILE:
                    break
            else:
                api.output.verbose_msg(
                    ['loading'], "SubPart {0} is None in cache of {1}... Trying to set ReadState".format(name, self.ID))
        return state

    ###
    def LoadStoredInfo(self):
        return glb.pnodes.GetStoredPNodeInfo(self)
        # md5=hashlib.md5()
        # md5.update(self.ID)
        # stored_data=datacache.GetCache("pnode-{0}".format(md5.hexdigest()))
        # return stored_data

    def StoreStoredInfo(self):
        info = self.GenerateStoredInfo()
        md5 = hashlib.md5()
        md5.update(self.ID)
        datacache.StoreData("pnode-{0}".format(md5.hexdigest()), info)

    def GenerateStoredInfo(self):

        # make new object
        info = part_info.part_info()

        # fill in object with data
        info.Name = self.__name
        info.ShortName = self.__short_name
        info.ID = self.ID
        info.ShortID = self.__short_alias
        info.Version = str(self.Version)
        info.RootID = self.__root.ID
        info.TargetPlatform = str(self.__env['TARGET_PLATFORM'])
        info.Config = str(self.__env['CONFIG'])
        info.PlatformMatch = str(self.__platform_match)
        info.ConfigMatch = self.__config_match
        info.PackageGroup = str(self.__package_group)
        info.Mode = self.__mode
        info.ForceLoad = self.ForceLoad

        # store subpart ID values
        info.SubPartIDs = list(self.__subparts.keys())

        tmp = []
        i = self.__parent
        if i is not None:
            info.ParentID = i.ID
        else:
            info.ParentID = None

        while i is not None:
            tmp.append(i.ID)
            i = i.Parent
        info.ParentIDs = tmp

        tmp = {'build': self.__classic_section}
        tmp.update(self.__sections)

        for k in tmp.keys():
            tmp[k] = tmp[k].ID
        info.SectionIDs = tmp

        tmp = {}
        if self.__file is None:
            pass
        else:
            tmp['name'] = self.__file.srcnode().ID  # check this
            tmp['csig'] = self.__file.get_csig()
            tmp['timestamp'] = self.__file.get_timestamp()
        info.File = tmp
        info.SrcPath = self.__part_dir
        # direct sdk file data
        # file={}
        # if self.__sdk_file is None:
        #    file['name']=self.Parent._sdk_file.srcnode().path# check this
        #    file['csig']=self.Parent._sdk_file.get_csig()
        #    file['timestamp']=self.Parent._sdk_file.get_timestamp()
        #
        # else:
        #    file['name']=self.__sdk_file.srcnode().path# check this
        #    file['csig']=self.__sdk_file.get_csig()
        #    file['timestamp']=self.__sdk_file.get_timestamp()
        # data['sdkfile']=copy.copy(file)
        # info.sdk_file={} #???
        tmp = []
        for i in self.__build_context_files:
            if i is None:
                continue
            i = self.__env.File(i)
            # Make SCons store node info
            safe_visited_call(i)
            # see if node time stamp matches
            tmp.append(
                {
                    'name': i.abspath,
                    'csig': i.get_csig(),
                    'timestamp': i.get_timestamp()
                }
            )

        info.BuildContext = tmp

        # this is config context ( like build but for the config files)
        tmp = {}
        for k, v in self.__config_context_files.items():
            tmp[k] = []
            for f in v:
                i = self.__env.File(f)
                # Make SCons store node info
                safe_visited_call(i)
                # see if node time stamp matches
                tmp[k].append({
                    'name': i.abspath,
                    'csig': i.get_csig(),
                    'timestamp': i.get_timestamp()
                })
        info.ConfigContext = tmp
        #info.kw = common.wrap_to_string(self.__kw)
        1/0  # need to fix this
        try:
            scm_obj = self.__scm if self.__scm else self.__root.__scm
            info.scm_cache_filename = scm_obj._cache_filename
        except Exception:
            pass
        info.BuildTargets = self.BuildTargets
        return info

    # Depends API
    def map_component_info(self, comp_part):
        pass

    def LoadFromCache(self):

        info = self.Stored
        # check that stored data is exits
        # if info is None:
        # self.ReadFile()
        # return

        self.__alias = info.ID  # should be handled by _setup_
        self.__short_alias = info.ShortID  # should be handled by _setup_
        self.__root = info.Root  # should be handled by _setup_
        self.__force_load = info.ForceLoad
        if info.ParentID:
            # we might not be loading the parent.... so we for set the parent name from cache
            self._set_name(info.ShortName, info.Parent.Stored.Name)
        else:
            self._set_name(info.ShortName)

        if self.Version == '0.0.0':
            self.Version = version.version(info.Version)

        self.__platform_match = info.PlatformMatch  # should be handled by _setup_
        self.__config_match = info.ConfigMatch
        self.__package_group = info.PackageGroup  # should be handled by _setup_
        self.__mode = info.Mode  # ?? # should be handled by _setup_

        for i in info.SubPartIDs:
            self.__subparts[i] = glb.pnodes.GetPNode(i)
        self.__parent = info.Parent  # should be handled by _setup_
        # how to deal with this???
        # need to double check logic for this when full new formats section are working
        self.__sections = info.SectionIDs
        tmp = {}
        for k, v in info.SectionIDs.items():
            tmp[k] = glb.pnodes.GetPNode(v)
        self.__sections = tmp

        if not self.isSetup:
            # we don't have a environment created
            # copy the one from the root. it should be good enough
            # for anything we need for part loaded via cache
            self.__env = self.__root.Env.Clone()
            self.__is_setup = True

        self.BuildTargets = info.BuildTargets


# some util function

# def pcmp(x, y):
    # return cmp(x._order_value, y._order_value)


def complex_compare(v1, v2, env):
    if id(v1) == id(v2):  # Equal pointer point to equal objects
        return False
    elif not isinstance(v1, type(v2)):
        return True
    elif isinstance(v1, SCons.Action.ActionBase):
        # get a genstring value as this will tell us if the
        # base action is different or not, cannot do more than this
        # as we may not have enough data defined for stuff to resolve correctly
        r1 = v1.genstring(["fake_target"], ["fake_source"], env)
        r2 = v1.genstring(["fake_target"], ["fake_source"], env)
        return r1 != r2
    elif isinstance(v1, type):
        return True if (v1.__module__, v1.__name__) != (v2.__module__, v2.__name__) else False
    elif isinstance(v1, types.FunctionType):
        return True if (v1.__module__, v1.__name__) != (v2.__module__, v2.__name__) else False
    elif util.isDictionary(v1):
        return v1 != v2
    elif util.isList(v1) or util.isTuple(v1):
        if len(v1) != len(v2):
            return True
        for i, j in zip(v1, v2):
            if complex_compare(i, j, env):
                return True
            return False
    # elif isinstance(v1, types.InstanceType):
        # if v1 == v2:
            # return False
        # elif str(v1) == str(v2):
            # return False
        # return True
    elif v1 != v2:
        return True
    return False


def diff_env(env, env2, ignore_keys=[]):
    '''returns set of kv that are different in env2'''
    skip = frozenset(['BUILDERS', 'ARCHITECTURE', 'config', 'CONFIG',
                      'PREPROCESS_LOGIC_QUEUE'] + ignore_keys)  # stuff to skip testing
    d1 = env.Dictionary()
    d2 = env2.Dictionary()

    s1 = set(d1.keys())
    s2 = set(d2.keys())

    ret = {}
    diff_keys = (s1 ^ s2) - skip  # what key are not in the common set
    for k in diff_keys:
        ret[k] = d1.get(k, d2.get(k, "Not defined in Both environments"))
    common_keys = (s1 & s2) - skip  # what keys both env have

    d1.fromkeys(common_keys)
    d2.fromkeys(common_keys)

    for k in common_keys:
        if complex_compare(d1[k], d2[k], env):
            ret[k] = d2[k]
    return ret


pnode_manager.manager.RegisterNodeType(Part)
