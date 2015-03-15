######################################
### as compiler configurations default
######################################

from parts.config import *

def map_default_version(env):
    return env('BINUTILS_VERSION')
    
config=configuration(map_default_version)

config.VersionRange("2-*",
                    prepend=ConfigValues(
                        ASPPFLAGS=['-m32'],
                        LINKFLAGS=['-m32']
                        )
                    )
