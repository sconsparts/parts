######################################
# Intel win32 compiler configurations release
######################################

from parts.config import *


def map_default_version(env):
    return env['INTELC_VERSION']


config = configuration(map_default_version)

config.VersionRange("7-*",
                    append=ConfigValues(
                        CCFLAGS=['/nologo', '/Ox', '/MD', '/W3'],
                        CXXFLAGS=['/EHsc', '/GR'],
                        CPPDEFINES=['NDEBUG']
                    )
                    )
