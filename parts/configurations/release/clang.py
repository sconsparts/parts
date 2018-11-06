######################################
# g++ compiler configurations release
######################################
from __future__ import absolute_import, division, print_function

from parts.config import *


def map_default_version(env):
    return env['CLANG_VERSION']


config = configuration(map_default_version)

config.VersionRange("3-*",
                    append=ConfigValues(
                        CCFLAGS=['-O2'],
                        CPPDEFINES=['NDEBUG']
                    )
                    )
