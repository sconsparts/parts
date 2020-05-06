######################################
# Intel win32 compiler configurations pat_debug
######################################


from parts.config import *


def map_default_version(env):
    return env['INTELC_VERSION']


config = configuration(map_default_version)

config.VersionRange("7-*",
                    append=ConfigValues(
                        CCFLAGS=['/nologo', '/Od', '/MDd', '/W3', '/RTC1'],
                        CXXFLAGS=['/EHsc', '/GR'],
                        CPPDEFINES=['DEBUG']
                    )
                    )
