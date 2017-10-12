######################################
# gcc compiler configurations for android
######################################

from parts.config import *


def map_default_version(env):
    return env['GXX_VERSION']

config = configuration(map_default_version)

config.VersionRange("3-*",
                    append=ConfigValues(
                        CCFLAGS=[
                            '--sysroot=${GXX.SYS_ROOT}',
                            '-O0',
                            '-mfloat-abi=softfp',
                        ],
                        CPPDEFINES=['DEBUG', "${_ANDROID_STL('CPPDEFINES')}"],
                        CPPPATH=["${_ANDROID_STL('CPPPATH')}"],
                        CXXFLAGS=["${_ANDROID_STL('CXXFLAGS')}"],
                        LINKFLAGS=[
                            '--sysroot=${GXX.SYS_ROOT}',
                            '-Wl,--fix-cortex-a8'
                        ],
                        LIBPATH=[
                            "${_ANDROID_STL('LIBPATH')}"
                        ],
                        LIBS=["${_ANDROID_STL('LIBS')}"]
                    )
                    )
