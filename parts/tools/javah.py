from __future__ import absolute_import, division, print_function

from Common.java import java
from SCons.Tool import javah


def generate(env, *args, **kw):

    java.MergeShellEnv(env)

    javah.generate(env, *args, **kw)


def exists(env):
    return javah.exists(env)

# vim: set et ts=4 sw=4 ai :
