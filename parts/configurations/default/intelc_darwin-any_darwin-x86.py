######################################
### Intel compiler configurations default-darwin
######################################

from parts.config import *
from intelc_darwin import config

config.VersionRange("*",
        append=ConfigValues(
            CCFLAGS=['-arch', 'i386', '-m32'],
            LINKFLAGS=['-arch', 'i386', '-m32'],
            )
        )
