# import c++ core toolchain
from __future__ import absolute_import, division, print_function

import parts.tools.cc
import parts.tools.Common
import parts.tools.GnuCommon
import SCons.Tool.cc

cplusplus = __import__('c++', globals(), locals(), [])


# import c core toolchain


def generate(env):
    """
    Add Builders and construction variables for CLang compilers
    to an Environment.
    """

    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)

    # get the basic C++ flags (unix based stuff only??)
    cplusplus.generate(env)
    parts.tools.cc.generate(env)

    # set up shell env for running compiler
    parts.tools.GnuCommon.clang.MergeShellEnv(env)

    env['CC'] = parts.tools.Common.toolvar('clang', ('clang',), env=env)
    env['CXX'] = parts.tools.Common.toolvar('clang++', ('clang++',), env=env)

    env['SHOBJSUFFIX'] = '.pic.o'
    env['OBJSUFFIX'] = '.o'

    env['SHCCFLAGS'] = SCons.Util.CLVar('$CCFLAGS -fPIC')


def exists(env):
    return parts.tools.GnuCommon.clang.Exists(env)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
