######################################
# gcc compiler configurations debug
######################################
from __future__ import absolute_import, division, print_function

from parts.config import *


def map_default_version(env):
    return env['GCC_VERSION']


config = configuration(map_default_version)

config.VersionRange("3-*",
                    append=ConfigValues(
                        CCFLAGS=['-O0', '-g'],
                        CPPDEFINES=['DEBUG']
                    )
                    )
