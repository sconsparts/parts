# import c++ core toolchain


import parts.tools.cc
import parts.tools.Common
import parts.tools.GnuCommon
import SCons.Tool.cc
import SCons.Util

cplusplus = __import__('c++', globals(), locals(), [])


# import c core toolchain


def generate(env):
    """
    Add Builders and construction variables for emcc wasm compilers
    to an Environment.
    """

    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)

    # get the basic C++ flags (unix based stuff only??)
    cplusplus.generate(env)
    parts.tools.cc.generate(env)

    # set up shell env for running compiler
    parts.tools.GnuCommon.emsdk.MergeShellEnv(env)

    env['CC'] = parts.tools.Common.toolvar('emcc', ('emcc',), env=env)
    env['CXX'] = parts.tools.Common.toolvar('em++', ('em++',), env=env)

    env['SHOBJSUFFIX'] = '.pic.o'
    env['OBJSUFFIX'] = '.o'

    env['SHCCFLAGS'] = SCons.Util.CLVar('$CCFLAGS -fPIC')


def exists(env):
    return parts.tools.GnuCommon.emsdk.Exists(env)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
