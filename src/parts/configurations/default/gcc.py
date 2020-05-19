######################################
# gcc compiler configurations default
######################################


from parts.config import *


def map_default_version(env):
    return env['GCC_VERSION']


config = configuration(map_default_version)

config.VersionRange(
    "*",
    replace=ConfigValues(
        _RPATHSTR='${JOIN("$RUNPATHS",":")}',
        RPATHLINK=[],
        _RPATHLINKSTR='${MAKEPATH("$RPATHLINK",":",False,True)}',
        _ABSRPATHLINKSTR='${MAKEPATH("$RPATHLINK",":",True,True)}',
        _RPATHLINK='${_concat("-Wl,-rpath-link=", _RPATHLINKSTR, "", __env__)}',
        _ABSRPATHLINK='${_concat("-Wl,-rpath-link=", _ABSRPATHLINKSTR, "", __env__)}',
        _RUNPATH='${_concat(RPATHPREFIX, _RPATHSTR, RPATHSUFFIX, __env__)}',
        _RPATH='$_RUNPATH $_RPATHLINK',
        _ABSRPATH='$_RUNPATH $_ABSRPATHLINK',
        RUNPATHS='${GENRUNPATHS()}',
        RPATHSUFFIX=",--enable-new-dtags",
    ),
)
