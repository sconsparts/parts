######################################
# Intel compiler configurations default-darwin
######################################
from __future__ import absolute_import, division, print_function

from intelc_darwin import config
from parts.config import *

config.VersionRange("*",
                    append=ConfigValues(
                        CCFLAGS=['-arch', 'i386', '-m32'],
                        LINKFLAGS=['-arch', 'i386', '-m32'],
                    )
                    )
