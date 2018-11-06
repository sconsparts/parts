######################################
# g++ compiler configurations debug
######################################
from __future__ import absolute_import, division, print_function

from parts.config import *


def map_default_version(env):
    return env['GXX_VERSION']


config = configuration(map_default_version)

config.VersionRange("3-*",
                    prepend=ConfigValues(
                        CCARCHFLAGS=['-m32'],
                        CCFLAGS=['-m32'],
                        LINKFLAGS=['-m32']
                    )
                    )
