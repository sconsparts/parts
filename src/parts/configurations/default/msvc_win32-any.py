######################################
# Microsoft compiler configurations default
######################################



from parts.config import *


def map_default_version(env):
    return env['MSVC_VERSION']


config = configuration(map_default_version)

config.VersionRange("6.0",
                    append=ConfigValues(
                        CPPDEFINES=['WIN32', '_WINDOWS'],
                        CCFLAGS=['/DMSVC_VERSION=$MSVC_VERSION']
                    )
                    )
config.VersionRange("7-*",
                    append=ConfigValues(
                        CPPDEFINES=['WIN32', '_WINDOWS'],
                        CCFLAGS=['/DMSVC_VERSION=$MSVC_VERSION']
                    )
                    )
