######################################
# g++ compiler configurations debug
######################################


from parts.config import *


def map_default_version(env):
    return env['GXX_VERSION']


config = configuration(map_default_version)

config.VersionRange(
    "*",
    # RUN_PATH setting for this platform toolchain
    replace=ConfigValues(
        _RPATHSTR='${JOIN("$RUNPATHS",":")}',
        RPATHLINK=[],
        _RPATHLINK='${_concat("-Wl,-rpath-link=", RPATHLINK, "", __env__, RDirs, TARGET, SOURCE)}',
        _ABSRPATHLINK='${_concat("-Wl,-rpath-link=", RPATHLINK, "", __env__, ABSDir, TARGET, SOURCE)}',
        _RUNPATH='${_concat(RPATHPREFIX, _RPATHSTR, RPATHSUFFIX, __env__)}',
        _RPATH='$_RUNPATH $_RPATHLINK',
        _ABSRPATH='$_RUNPATH $_ABSRPATHLINK',
        RUNPATHS='${GENRUNPATHS()}',
        RPATHSUFFIX=",--enable-new-dtags",
    ),
)
