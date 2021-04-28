
import parts.api as api

import SCons.Script
from SCons.Debug import logInstanceCreation


class map_build_context:
    '''
        This maps all build info related files we might need to help detect quickly
    if the build context has changed from the last run.

    This is used for faster loading via cache logic
    This is turned off at the moment...
    '''

    def __init__(self, pobj: 'part.Part'):
        if __debug__:
            logInstanceCreation(self)
        self.pobj = pobj

    def __call__(self):

        self.pobj._build_context_files.update(self.pobj.Env['_BUILD_CONTEXT_FILES'])
        self.pobj._config_context_files.update(self.pobj.Env['_CONFIG_CONTEXT'])


# add configuration variables
api.register.add_bool_variable('AUTO_RPATH', True, 'Controls if RPath values are automatically added to path')
