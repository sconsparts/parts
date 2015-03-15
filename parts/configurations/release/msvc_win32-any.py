######################################
### Microsoft compiler configurations release
######################################

from parts.config import *

def map_default_version(env):
    return env['MSVC_VERSION']
    

config=configuration(map_default_version)

config.VersionRange("6.0",
                    append=ConfigValues(
                        CCFLAGS=['/nologo','/Ox','/MD','/W3'],
                        CXXFLAGS=['/EHsc','/GR'],
                        CPPDEFINES=['NDEBUG']
                        )
                    )
config.VersionRange("7-*",
                    append=ConfigValues(
                        CCFLAGS=['/nologo','/Ox','/MD','/W3'],
                        CXXFLAGS=['/EHsc','/GR'],
                        CPPDEFINES=['NDEBUG']
                        )
                    )

