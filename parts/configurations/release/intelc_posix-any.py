######################################
# Intel posix compiler configurations release
######################################

from parts.config import *


def map_default_version(env):
    return env['INTELC_VERSION']


config = configuration(map_default_version)


config.VersionRange("7-*",
                    append=ConfigValues(
                        CCFLAGS=['-O2'],
                        CPPDEFINES=['NDEBUG']
                    )
                    )
