

import SCons.Tool.cc


def generate(env):
    SCons.Tool.cc.generate(env)

    env.SetDefault(CCCOM='${TEMPFILE("$CC -o $TARGET -c $CFLAGS $CCFLAGS $_CCCOMCOM $SOURCES $CCARCHFLAGS","$CCCOMSTR")}')
    env.SetDefault(SHCCCOM='${TEMPFILE("$SHCC -o $TARGET -c $SHCFLAGS $SHCCFLAGS $_CCCOMCOM $SOURCES $CCARCHFLAGS","$SHCCCOMSTR")}')

    env.SetDefault(SYSINCPREFIX='$INCPREFIX')
    env.SetDefault(SYSINCSUFFIX='$INCSUFFIX')

    # System include paths: dirs in SYSCPPPATH are emitted with $SYSINCPREFIX
    # (gcc/clang set this to -isystem) instead of -I, so a part can suppress
    # warnings from a dependency's headers. SYSINCPREFIX defaults to $INCPREFIX
    # here, so on a toolchain that does not set it this is a harmless no-op
    # (SYSCPPPATH behaves like CPPPATH). The flags are only added when SYSCPPPATH
    # is non-empty.
    env.SetDefault(SYSCPPPATH=[])
    env.SetDefault(_CPPSYSINCFLAGS='$( ${_concat(SYSINCPREFIX, SYSCPPPATH, SYSINCSUFFIX, __env__, RDirs, TARGET, SOURCE)} $)')
    if '$_CPPSYSINCFLAGS' not in env['_CCCOMCOM']:
        env['_CCCOMCOM'] += ' $_CPPSYSINCFLAGS'


exists = SCons.Tool.cc.exists

# vim: set et ts=4 sw=4 ai ft=python :
