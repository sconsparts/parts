######################################
### gcc compiler configurations default
######################################

from parts.config import *

def map_default_version(env):
    return env['GCC_VERSION']
    
config=configuration(map_default_version)

config.VersionRange("3-*",
                    prepend=ConfigValues(
                        CCARCHFLAGS=['-m64'],
                        CCFLAGS=['-m64']
                        )
                    )
