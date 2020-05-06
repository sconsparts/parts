

import parts.tools.Common
import SCons.Defaults
from parts.api import output
from parts.tools.MSCommon.wix import (createMsiBuilder, createWixObjectBuilder,
                                      wix)


def generate(env):

    wixObject = createWixObjectBuilder(env)
    msi = createMsiBuilder(env)

    env['WIX_TOOL_PATHS'] = ['${WIX.INSTALL_ROOT}']  # This variable is used by wixEnvScanner to find exts

    env['WIXPPPATH'] = []
    env['WIXPPPATHPREFIX'] = '-I'
    env['WIXPPPATHSUFFIX'] = ''
    env['_WIXPPFLAGS'] = '$( ${_concat(WIXPPPATHPREFIX, WIXPPPATH, WIXPPPATHSUFFIX, __env__, lambda x: [x.abspath for x in RDirs(x)], TARGET, SOURCE)} $)'
    env['WIXPPDEFINES'] = []
    env['WIXPPDEFPREFIX'] = '-d'
    env['WIXPPDEFSUFFIX'] = ''
    env['_WIXPPDEFFLAGS'] = '${_defines(WIXPPDEFPREFIX, WIXPPDEFINES, WIXPPDEFSUFFIX, __env__)}'
    env['WIXCLCOM'] = '$WIXCL $_WIXPPFLAGS $WIXCLFLAGS $_WIXPPDEFFLAGS -o $TARGET $SOURCE'

    env['WIXOBJPREFIX'] = ''
    env['WIXOBJSUFFIX'] = '.wixobj'

    env['WIXLINKEXTPREFIX'] = ''
    env['WIXLINKEXTSUFFIX'] = '.dll'
    env['_nodes_to_strs'] = lambda prefix, list, suffix, env: [
        str(x) for x in SCons.Defaults._concat_ixes(prefix, list, suffix, env)]
    env['_WIXEXTSTRS'] = '${_nodes_to_strs(WIXLINKEXTPREFIX, WIXLINKEXTENSIONS, WIXLINKEXTSUFFIX, __env__)}'
    env['_WIXLINKEXTENSIONS'] = '${_defines("-ext ", _WIXEXTSTRS, "", __env__)}'

    env['_WIXLCLSTRS'] = '${[x.abspath for x in __env__.arg2nodes(WIXLOCALIZATION)]}'
    env['_WIXLOCALIZATION'] = '${_defines("-loc ", _WIXLCLSTRS, "", __env__)}'

    env['WIXFILEPATH'] = ['$SRC_DIR']
    env['WIXFILEDIRPREFIX'] = '-b '  # Do not remove trailing space
    env['WIXFILEDIRSUFFIX'] = ''
    env['_WIXFILEDIRFLAGS'] = '$( ${_concat(WIXFILEDIRPREFIX, WIXFILEPATH, WIXFILEDIRSUFFIX, __env__, RDirs, TARGET, SOURCE)} $)'
    env['WIXLINKCOM'] = '$WIXLINK $WIXLINKFLAGS $_WIXLINKEXTENSIONS $_WIXFILEDIRFLAGS $_WIXLOCALIZATION -o $TARGET $SOURCES'

    env['MSIPREFIX'] = ''
    env['MSISUFFIX'] = '.msi'

    wix.MergeShellEnv(env)
    env['HEAT'] = parts.tools.Common.toolvar('heat', ('heat', 'wix'), env=env)
    env['WIXCL'] = parts.tools.Common.toolvar('candle', ('candle', 'wix'), env=env)
    env['WIXLINK'] = parts.tools.Common.toolvar('light', ('light', 'wix'), env=env)


def exists(env):
    return wix.Exists(env)

# vim: set et ts=4 sw=4 ft=python :
