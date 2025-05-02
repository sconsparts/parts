######################################
# emsdk compiler configurations default
######################################


from parts.config import *


def map_default_version(env):
    return env['EMSDK_VERSION']


config = configuration(map_default_version)

config.VersionRange(
    "*",
    # RUN_PATH setting for this platform toolchain
    replace=ConfigValues(
#        _RPATHSTR='${JOIN("$RUNPATHS",":")}',
        RPATHLINK=[],
#        _RPATHLINKSTR='${MAKEPATH("$RPATHLINK",":",False)}',
#        _ABSRPATHLINKSTR='${MAKEPATH("$RPATHLINK",":",True)}',
#        _RPATHLINK='${_concat("-Wl,-rpath-link=", _RPATHLINKSTR, "", __env__)}',
#        _ABSRPATHLINK='${_concat("-Wl,-rpath-link=", _ABSRPATHLINKSTR, "", __env__)}',
        _RUNPATH='${_concat(RPATHPREFIX, _RPATHSTR, RPATHSUFFIX, __env__)}',
        _RPATH='$_RUNPATH $_RPATHLINK',
        _ABSRPATH='$_RUNPATH $_ABSRPATHLINK',
        RUNPATHS='${GENRUNPATHS()}',
#        RPATHSUFFIX=",--enable-new-dtags",
    ),
)
