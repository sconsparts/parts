#Stub file to update env for ar tool

import SCons.Tool.ar
import parts.tools.GnuCommon.binutils
import parts.tools.GnuCommon.common
import parts.tools.Common

def generate(env):
    parts.tools.GnuCommon.binutils.setup(env)

    SCons.Tool.ar.generate(env)
    parts.tools.GnuCommon.common.makeStdBinutilsTool(env, 'AR', ['ar'])
    parts.tools.GnuCommon.common.makeStdBinutilsTool(env, 'RANLIB', ['ranlib'])
    try:
        env['ARCOM'] = env.get('BINUTILS', {}).get('ARCOM', env['ARCOM'])
    except KeyError:
        pass


def exists(env):
    parts.tools.GnuCommon.binutils.setup(env)
    return SCons.Tool.ar.exists(env)

# vim: set et ts=4 sw=4 ai ft=python :

