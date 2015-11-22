######################################
### gcc compiler configurations debug
######################################

from parts.config import *

def map_default_version(env):
    return env['GCC_VERSION']
    
config=configuration(map_default_version)

config.VersionRange("3-*",
                    append=ConfigValues(
                        CPPDEFINES=['THIS_IS_A_CUSTOM_VALUE']
                        )
                    )

