
from typing import List, Union, Optional

import parts.api as api
import parts.common as common
import parts.glb as glb
from parts.core import util
from parts.pnode import part

from .base import base


class reuse_part_scm(base):
    """This object allow users to reuse the checkout location of another Part

    In Parts this will be seen as ScmReuse. The old name of ScmUsePriorPart will be mapped this.
    This class is basically a proxy class.
    """
    __slots__ = [
        '_partref',
        '_scm'
    ]

    def __init__(self, part):
        super().__init__("", "")
        self._partref = part
        self._scm = None

    @property
    def Server(self):
        '''Forward the scm server value
        '''
        return self._scm.Server

    @property
    def Repository(self):
        '''Forward the scm server value
        '''
        return self._scm.Repository

    @property
    def FullPath(self):
        ''' returns the full path'''
        return self._scm.FullPath

    @property
    def CheckOutDir(self):
        '''Forward the scm check out directory value
        '''
        return self._scm.CheckOutDir

    # @property
    # def PartFileName(self):
    #    '''Forward the scm file name value
    #    '''
    #    return self._scm.PartFileName

    @property
    def PartFileExists(self):
        '''Forward the scm file exists value
        '''
        return self._scm.PartFileExists

    def AllowParallelAction(self):
        '''Forward the scm parallel action value
        '''
        return self._scm.AllowParallelAction

    def UpdateEnv(self):
        '''
        fixme
        '''
        # when we setup this object we want
        # get the real scm object so we can proxy it
        if isinstance(self._partref, part.Part):
            self._scm = self._partref.Scm
        elif util.isString(self._partref):
            # assume this is a part alias
            tmpalias = None
            if self._env['ALIAS_POSTFIX'] or self._env['ALIAS_PREFIX']:
                tmpalias = "{0}{1}{2}".format(self._env.subst('$ALIAS_PREFIX'), self._partref, self._env.subst('$ALIAS_POSTFIX'))
            tmp = glb.engine._part_manager._from_alias(self._partref)
            if tmp is None and tmpalias:
                tmp = glb.engine._part_manager._from_alias(tmpalias)
            if tmp is None:
                if tmpalias:
                    api.output.error_msg("Can not find Part that maps to the alias of {0} or {1}".format(self._partref, tmpalias))
                else:
                    api.output.error_msg("Can not find Part that maps to the alias of {0}".format(self._partref,))
            self._partref = tmp
            self._scm = self._partref.Scm
        else:
            api.output.error_msg('ScmReuse was unable to map the scm object to part "%s"' % (self._partref))
        self._env['SCM'] = self._scm._env['SCM'].clone()
        self._env['SCM_DIR'] = self._partref.Env.subst('$CHECK_OUT_DIR')

    def NeedsToUpdate(self):
        '''Forward the scm need to update value
        '''
        return self._scm.NeedsToUpdate()

    def do_update_check(self):
        '''Function that should be used by subclass to add to any custom update logic that should be checked'''

        return self._scm.do_update_check

    def do_exist_logic(self) -> Optional['str']:
        ''' call for testing if the scm think the stuff exists

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        return self._scm.do_exist_logic

    def do_check_logic(self) -> Optional['str']:
        ''' call for checking if what we have in the data cache is matching the current checkout request
        in the SConstruct match up

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        return self._scm.do_check_logic

    def do_force_logic(self) -> Optional['str']:
        ''' call for testing if what is one disk matches what the SConstruct says should be used

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        return self._scm.do_force_logic

    def UpdateOnDisk(self):
        '''Forward the scm update logic
        '''
        return self._scm.UpdateOnDisk()

    def clean_step(self, out_dir):
        '''Forward the scm clean logic
        '''
        return self._scm._clean_step(out_dir)

    def UpdateAction(self, out_dir):
        '''Forward the scm update action value
        '''
        return self._scm.UpdateAction()

    def CheckOutAction(self, out_dir):
        '''Forward the scm check out action value
        '''
        return self._scm.CheckOutAction()

    def Update(self):
        '''Forward the scm update logic'''
        return self._scm.Update()

    def CheckOut(self):
        '''Forward the scm update logic'''
        return self._scm.CheckOut()

    def ProcessResult(self, result):
        ''' this function returns the result of the given action call.

        @param result True or False based on if the Update logic was able to finish a successfull update

        Allow the a scm upbject to setup an last minute state that it wants to. or store any data that might be needed
        for the next run
        '''
        return self._scm.ProcessResult(result)

    def PostProcess(self):
        ''' This function is called when the system is done updating the disk
        This allows the object to update an data it needs on disk, or in the environment
        '''
        self._scm.PostProcess()
        self._env['SCM'] = self._scm._env['SCM'].clone()

    @property
    def _cache_filename(self):
        return self._scm._cache_filename


api.register.add_global_object('VcsReuse', reuse_part_scm)
api.register.add_global_object('VcsUsePriorPart', reuse_part_scm)
api.register.add_global_object('ScmReuse', reuse_part_scm)
