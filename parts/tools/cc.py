from __future__ import absolute_import, division, print_function

import SCons.Tool.cc


def generate(env):
    SCons.Tool.cc.generate(env)

    env.SetDefault(CCCOM='${TEMPFILE("$CC -o $TARGET -c $CFLAGS $CCFLAGS $_CCCOMCOM $SOURCES $CCARCHFLAGS")}')
    env.SetDefault(SHCCCOM='${TEMPFILE("$SHCC -o $TARGET -c $SHCFLAGS $SHCCFLAGS $_CCCOMCOM $SOURCES $CCARCHFLAGS")}')


exists = SCons.Tool.cc.exists

# vim: set et ts=4 sw=4 ai ft=python :
