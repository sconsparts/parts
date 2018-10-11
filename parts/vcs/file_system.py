from base import base
from .. import common
from ..core import util
from .. import api
import SCons.Defaults
import os


class file_system(base):
    """Allows thr retrieval of items from a file based system

    Mapped as VcsFileSystem and VcsPreBuilds
    """
    __slots = []

    @base.Server.getter
    def Server(self):
        ''' svn property override to getting server data'''
        tmp = None
        if self._server is not None:
            tmp = self._server
        tmp = self._env['FILE_SYSTEM_SERVER']
        if tmp == '':
            tmp = self._env['PREBUILT_SERVER']
            if tmp != '':
                api.output.warning_msg("PREBUILT_SERVER is deprecated. Please use FILE_SYSTEM_SERVER instead", show_stack=False)
        return tmp

    @base.FullPath.getter
    def FullPath(self):
        ''' returns the full path (server + repository)

        We override this as we don't want to change the paths from \ to / on windows
        '''
        return os.path.normpath(os.path.join(self.Server, self.Repository))

    def UpdateAction(self, out_dir):
        ''' The file system update action

        Currently is implemented in term of SCons default Actions
        '''

        cmdlst = [
            SCons.Defaults.Delete(out_dir, False),
            SCons.Defaults.Copy(out_dir, self.FullPath)
        ]
        return self._env.Action(cmdlst, "VcsFileSystem: Updating Files from %s to %s" % (self.FullPath, out_dir))

    def CheckOutAction(self, out_dir):
        ''' The file system check out action

        Currently is implemented in term of SCons default Actions
        '''

        cmdlst = [
            SCons.Defaults.Delete(out_dir, False),
            # SCons.Defaults.Mkdir(self.FullPath),
            SCons.Defaults.Copy(out_dir, self.FullPath)
        ]
        return self._env.Action(cmdlst, "VcsFileSystem: Copying Files from %s to %s" % (self.FullPath, out_dir))

    def UpdateEnv(self):
        '''
        Update the with information about the current VCS object
        '''
        self._env['VCS'] = common.namespace(
            TYPE='file_system',
            CHECKOUT_DIR='$VCS_FILESYSTEM_DIR',
        )

    def do_exist_logic(self):
        ''' call for testing if the vcs think the stuff exists

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        if self.PartFileExists:
            return None
        return "%s needs to be updated on disk" % self._pobj.Alias

    def do_check_logic(self):
        ''' call for checking if what we have in the data cache is matching the current checkout request
        in the SConstruct match up

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        return self.do_exist_logic()

    def do_force_logic(self):
        ''' call for testing if what is one disk matches what the SConstruct says should be used

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        return self.do_exist_logic()

    @property
    def _cache_filename(self):
        return None  # No cache file is stored for file system object

    @base.CacheFileExists.getter
    def CacheFileExists(self):
        return True


api.register.add_variable('VCS_FILESYSTEM_DIR', '${CHECK_OUT_ROOT}/${PART_ALIAS}', 'Full path used for any given checked out item')
api.register.add_variable('VCS_PREBUILDS_DIR', '${VCS_FILESYSTEM_DIR}', '')  # compatibility

api.register.add_variable('FILE_SYSTEM_SERVER', '', '')
api.register.add_variable('PREBUILT_SERVER', '', '')  # compatibility

api.register.add_global_object('VcsFileSystem', file_system)
api.register.add_global_object('VcsPreBuilt', file_system)  # compatibility
