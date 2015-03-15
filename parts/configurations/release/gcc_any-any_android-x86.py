######################################
### gcc compiler configurations for android 
######################################

from parts.config import *

def map_default_version(env):
    return env['GXX_VERSION']
    
config=configuration(map_default_version)

config.VersionRange("3-*",
                    append=ConfigValues(
                        CCFLAGS=[
                                '-O2',
                                '--sysroot=${GXX.SYS_ROOT}'
                            ],
                        CPPDEFINES=['NDEBUG'],
                        LINKFLAGS=[
                                '--sysroot=${GXX.SYS_ROOT}'
                                ]
                        )
                    )

