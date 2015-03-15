######################################
### GNU linker configurations 
######################################


from parts.config import *

def map_default_version(env):
    return env['GCC_VERSION']

config = configuration(map_default_version)

config.VersionRange("*",
                    prepend=ConfigValues(
                        LINKFLAGS=['-m32']
                        )
                    )

