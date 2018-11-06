######################################
# gcc compiler configurations for android
######################################
from __future__ import absolute_import, division, print_function

from parts.config import *


def map_default_version(env):
    return env['GXX_VERSION']


config = configuration(map_default_version)

config.VersionRange("3-*",
                    append=ConfigValues(
                        CCFLAGS=[
                            '-O0',
                            '--sysroot=${GXX.SYS_ROOT}'
                        ],
                        CPPDEFINES=['DEBUG', "${_ANDROID_STL('CPPDEFINES')}"],
                        CPPPATH=["${_ANDROID_STL('CPPPATH')}"],
                        CXXFLAGS=["${_ANDROID_STL('CXXFLAGS')}"],
                        LINKFLAGS=[
                            '--sysroot=${GXX.SYS_ROOT}'
                        ],
                        LIBPATH=[
                            "${_ANDROID_STL('LIBPATH')}"
                        ],
                        LIBS=["${_ANDROID_STL('LIBS')}"]
                    )
                    )
