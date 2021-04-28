######################################
# gcc compiler configurations debug
######################################


from parts.config import *


def map_default_version(env):
    return env['GCC_VERSION']


config = configuration(map_default_version)

config.VersionRange("3-7",
                    append=ConfigValues(
                        CCFLAGS=['-O0', '-g'],
                        CPPDEFINES=['DEBUG']
                    )
                    )

config.VersionRange("7-*",
                    append=ConfigValues(
                        CCFLAGS=['-fdiagnostics-color=always', '-O2'],
                        CPPDEFINES=['NDEBUG']
                    )
                    )
