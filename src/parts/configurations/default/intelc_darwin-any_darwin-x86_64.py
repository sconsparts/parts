######################################
# Intel compiler configurations default-darwin
######################################
from __future__ import absolute_import, division, print_function

from intelc_darwin import config
from parts.config import *

config.VersionRange("*",
                    append=ConfigValues(
                        CCFLAGS=['-arch', 'x86_64', '-m64'],
                        LINKFLAGS=['-arch', 'x86_64', '-m64'],
                    )
                    )
