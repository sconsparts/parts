######################################
### Microsoft compiler configurations pat_debug
######################################

from parts.config import *

def map_default_version(env):
    return env['MSVC_VERSION']
    

config=configuration(map_default_version)

config.VersionRange("6.0",
                    append=ConfigValues(
                        CPPDEFINES=['THIS_IS_A_CUSTOM_VALUE']
                        )
                    )
config.VersionRange("7-*",
                    append=ConfigValues(
                        CPPDEFINES=['THIS_IS_A_CUSTOM_VALUE']
                        )
                    )
