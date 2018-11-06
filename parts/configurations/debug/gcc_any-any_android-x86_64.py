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
                        CPPDEFINES=['DEBUG'],
                        LINKFLAGS=[
                            '--sysroot=${GXX.SYS_ROOT}'
                        ]
                    )
                    )
