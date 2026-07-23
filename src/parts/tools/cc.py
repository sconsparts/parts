

import SCons.Tool.cc


def generate(env):
    SCons.Tool.cc.generate(env)

    # Optional compiler launcher prefixed to the C compile command (e.g. ccache
    # or sccache). Empty by default, so it adds nothing unless a toolchain or site
    # sets it. Kept separate from $CC so $CC stays a clean compiler path for
    # consumers that inspect it (e.g. -DCMAKE_C_COMPILER=$CC in the CMake piece).
    env.SetDefault(CC_LAUNCHER='')

    # Assign (not SetDefault): SCons.Tool.cc.generate() above already set
    # CCCOM/SHCCCOM via a direct env[] assignment, so SetDefault here was a silent
    # no-op and these parts templates never applied -- C compiles fell back to the
    # base SCons command, bypassing the TEMPFILE response-file wrapping (and
    # $CCARCHFLAGS) that the parts C++ command already gets. c++.py does not call
    # the base generate(), which is why its SetDefault(CXXCOM) works; this brings
    # the C path in line with C++.
    env['CCCOM'] = '${TEMPFILE("$CC_LAUNCHER $CC -o $TARGET -c $CFLAGS $CCFLAGS $_CCCOMCOM $SOURCES $CCARCHFLAGS","$CCCOMSTR")}'
    env['SHCCCOM'] = '${TEMPFILE("$CC_LAUNCHER $SHCC -o $TARGET -c $SHCFLAGS $SHCCFLAGS $_CCCOMCOM $SOURCES $CCARCHFLAGS","$SHCCCOMSTR")}'

    env.SetDefault(SYSINCPREFIX='$INCPREFIX')
    env.SetDefault(SYSINCSUFFIX='$INCSUFFIX')


exists = SCons.Tool.cc.exists

# vim: set et ts=4 sw=4 ai ft=python :
