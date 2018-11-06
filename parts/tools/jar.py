from __future__ import absolute_import, division, print_function

from Common.java import java
from SCons.Tool import jar


def generate(env, *args, **kw):

    java.MergeShellEnv(env)

    jar.generate(env, *args, **kw)


def exists(env):
    return jar.exists(env)

# vim: set et ts=4 sw=4 ai :
