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
                                '--sysroot=${GXX.SYS_ROOT}',
                                '-O2',
                                '-march=armv7-a',
                                '-mfloat-abi=softfp',
                            ],
                        CPPDEFINES=['NDEBUG'],
                        LINKFLAGS=[
                                '--sysroot=${GXX.SYS_ROOT}',
                                '-Wl,--fix-cortex-a8'
                                   ]
                        )
                    )

