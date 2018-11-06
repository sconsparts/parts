# defines tools chain wdk
from __future__ import absolute_import, division, print_function


def wdk_setup(env, ver):
    env['WDK_VERSION'] = ver


def resolve(env, version):

    def func(x): return wdk_setup(x, version)
    return [
        ('wdk', func),
    ]
