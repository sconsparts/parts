from __future__ import absolute_import, division, print_function

import _thread

import parts.api as api
import parts.common as common
import parts.core as core
import parts.glb as glb
import parts.mappers as mappers
import parts.requirement as requirement
import SCons.Script
from SCons.Debug import logInstanceCreation


class map_build_context(object):
    '''
        This maps all build info related files we might need to help detect quickly
    if the build context has changed from the last run.

    This is used for faster loading via cache logic
    This is turned off at the moment...
    '''

    def __init__(self, pobj):
        if __debug__:
            logInstanceCreation(self)
        self.pobj = pobj

    def __call__(self):

        self.pobj._build_context_files.update(self.pobj.Env['_BUILD_CONTEXT_FILES'])
        self.pobj._config_context_files.update(self.pobj.Env['_CONFIG_CONTEXT'])


# add configuartion varaible
api.register.add_bool_variable('AUTO_RPATH', True, 'Controls if RPath values are automatically added to path')
