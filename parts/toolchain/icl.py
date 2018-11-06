# defines tools chain icl ( as in the Intel Compiler windows)
from __future__ import absolute_import, division, print_function


def icl_setup(env, ver):
    env['INTELC_VERSION'] = ver


def resolve(env, version):
    def func(x): return icl_setup(x, version)
    return [
        ('intelc', func)
    ]
