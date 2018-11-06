######################################
# as compiler configurations default
######################################
from __future__ import absolute_import, division, print_function

from parts.config import *


def map_default_version(env):
    return env['GCC_VERSION']


config = configuration(map_default_version)

config.VersionRange("*",
                    replace=ConfigValues(
                        PROGSUFFIX='',
                        INSTALL_BIN_PATTERN=['*'],
                        SDK_BIN_PATTERN=['*'],
                        # setup linux paths in tmp files
                        CCCOM='${TEMPFILE("$CC -o $TARGET -c $CFLAGS $CCFLAGS $_CCCOMCOM $SOURCES",force_posix_paths=True)}',
                        SHCCCOM='${TEMPFILE("$SHCC -o $TARGET -c $SHCFLAGS $SHCCFLAGS $_CCCOMCOM $SOURCES",force_posix_paths=True)}',
                    ),
                    )
