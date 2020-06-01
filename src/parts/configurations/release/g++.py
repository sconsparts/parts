######################################
# g++ compiler configurations release
######################################


from parts.config import *


def map_default_version(env):
    return env['GXX_VERSION']


config = configuration(map_default_version)

config.VersionRange("3-7",
                    append=ConfigValues(
                        CCFLAGS=['-O2'],
                        CPPDEFINES=['NDEBUG']
                    )
                    )

config.VersionRange("7-*",
                    append=ConfigValues(
                        CCFLAGS=['-fdiagnostics-color=always','-O2'],
                        CPPDEFINES=['NDEBUG']
                    )
                    )
