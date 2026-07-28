# emscripten (emsdk) toolchain: emcc / em++ wasm compilers


import os

import parts.tools.cc
import parts.tools.Common
import parts.tools.GnuCommon
import SCons.Tool.cc
import SCons.Util

cplusplus = __import__('c++', globals(), locals(), [])


def generate(env):
    """
    Add Builders and construction variables for the emcc/em++ wasm compilers
    to an Environment.
    """

    SCons.Tool.createObjBuilders(env)

    # get the basic C/C++ flag machinery (unix-style)
    cplusplus.generate(env)
    parts.tools.cc.generate(env)

    # make $EMSDK available to parts using this toolchain (the OS value emsdk_env.sh
    # exports; detection itself uses the EnvFinder in GnuCommon/emsdk.py)
    env.SetDefault(EMSDK=os.environ.get('EMSDK', ''))

    # set up shell env (PATH etc.) for running the emscripten compilers
    parts.tools.GnuCommon.emsdk.MergeShellEnv(env)

    env['CC'] = parts.tools.Common.toolvar('emcc', ('emcc',), env=env)
    env['CXX'] = parts.tools.Common.toolvar('em++', ('em++',), env=env)

    env['SHOBJSUFFIX'] = '.pic.o'
    env['OBJSUFFIX'] = '.o'

    env['SHCCFLAGS'] = SCons.Util.CLVar('$CCFLAGS -fPIC')


def exists(env):
    return parts.tools.GnuCommon.emsdk.Exists(env)

# vim: set et ts=4 sw=4 ai ft=python :
