######################################
# emsdk (emscripten) toolchain default configuration
######################################


from parts.config import *


def map_default_version(env):
    return env['EMSDK_VERSION']


config = configuration(map_default_version)

config.VersionRange(
    "*",
    replace=ConfigValues(
        RPATHLINK=[],
        _RUNPATH='${_concat(RPATHPREFIX, _RPATHSTR, RPATHSUFFIX, __env__)}',
        _RPATH='$_RUNPATH $_RPATHLINK',
        _ABSRPATH='$_RUNPATH $_ABSRPATHLINK',
        RUNPATHS='${GENRUNPATHS()}',
        # run the external build tools through emscripten's wrappers so the
        # configure/make/cmake steps target wasm (these are the generic build
        # wrapper hooks; emsdk ships emconfigure/emmake/emcmake on PATH)
        AUTO_MAKE_CONFIGURE_WRAPPER='emconfigure',
        AUTO_MAKE_MAKE_WRAPPER='emmake',
        CMAKE_WRAPPER='emcmake',
    ),
)
