######################################
### K1OM compiler configurations defaults for release
######################################

import sys
from parts.config import *
import SCons.Script

def map_default_version(env):
    return env['INTELC_VERSION']
    

config=configuration(map_default_version)

  
config.VersionRange("13-*",
                    append=ConfigValues(
                        CCFLAGS=['-O2'],
                        LINKFLAGS=['-static-intel'],
                        )
                    )     
					