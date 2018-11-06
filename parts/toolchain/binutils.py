
# defines tools chain for the general Gnu set( as needed for Intel Compiler posix or simular tools)
from __future__ import absolute_import, division, print_function


def _setup(env, ver):
    env['BINUTILS_VERSION'] = ver


def resolve(env, version):
    def func(x): return _setup(x, version)
    return [('ld', func, True)]
