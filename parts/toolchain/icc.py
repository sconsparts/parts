# defines tools chain icc ( as in the Intel Compiler posix)
from __future__ import absolute_import, division, print_function


def icc_setup(env, ver):
    env['INTELC_VERSION'] = ver


def resolve(env, version):
    def func(x): return icc_setup(x, version)
    return [
        ('intelc', func)
    ]
