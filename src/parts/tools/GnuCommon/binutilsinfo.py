

import parts.tools.Common
import SCons.Util
from parts.platform_info import SystemPlatform
from parts.tools.Common.Finders import EnvFinder, PathFinder, ScriptFinder
from parts.tools.Common.ToolInfo import ToolInfo
from SCons.Debug import logInstanceCreation

from . import android
from .common import GnuInfo, binutils


class BinutilInfo(GnuInfo):
    """
    We need this class be implemented because:
        a) Binutils tool info object does not modify env['ENV']['PATH'] variable value
        b) binutils tool info object has to force Parts to use binutils from the location
           explicitly specified by user via env['BINUTILS_INSTALL_ROOT '] value.
    """

    def __init__(self, install_scanner, opt_dirs, script, subst_vars, shell_vars, test_file, opt_pattern=None):
        super(self.__class__, self).__init__(install_scanner, opt_dirs, script, subst_vars, shell_vars, test_file, opt_pattern)

    def query(self, env, namespace, root_path, use_script):
        if 'BINUTILS_INSTALL_ROOT' in env:
            return super(self.__class__, self).query(env, namespace, env['BINUTILS_INSTALL_ROOT'], use_script)
        return super(self.__class__, self).query(env, namespace, root_path, use_script)

    def exists(self, env, namespace, version, root_path, use_script, tool=None):
        if root_path is None and 'BINUTILS_INSTALL_ROOT' in env:
            root_path = env['BINUTILS_INSTALL_ROOT']
        shell_env = self.get_shell_env(env, namespace, version, root_path, use_script, tool)
        try:
            if SCons.Util.WhereIs(env.subst('${BINUTILS.TOOL}'), path=[root_path] if root_path else None):
                return shell_env
        except KeyError:
            pass

        return None


class BinutilsSetupWrapper(object):

    def __init__(self, binutils):
        if __debug__:
            logInstanceCreation(self)
        self.__binutils = binutils

    def __call__(self, env):
        if env.subst('$TARGET_ARCH') in ('k1om', ) and env.get('OBJCOPY', '') in ('objcopy', ''):
            env['OBJCOPY'] = '${HOST_ARCH}-${TARGET_ARCH}-linux-objcopy'
        if 'BINUTILS_VERSION' in env or 'BINUTILS_INSTALL_ROOT' in env or env.get('HOST_OS') != env.get('TARGET_OS'):
            # We call it MergeShellEnv but don't be confused by its name because binutils ToolSetting objects do not
            # modify shell environment but only initialize BINUTILS namespace
            self.__binutils.MergeShellEnv(env)
            return True
        return False


binutils.setup = BinutilsSetupWrapper(binutils)

# We expect binutils be found in the dirs of form /opt/gcc/bin, /opt/gcc-4.1.1/bin
# /opt/binutils/bin, /opt/binutils-2.19.1/bin.
binutils_pattern = r'(binutils|gcc)(-\d+(\.\d+)*)?'

binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'x86'), SystemPlatform('posix', 'x86_64'), SystemPlatform('freebsd', 'x86_64')],
    targets=[SystemPlatform('posix', 'x86'), SystemPlatform('posix', 'x86_64'), SystemPlatform('freebsd', 'x86_64')],
    info=[
        BinutilInfo(
            # standard location, however there might be
            # some posix offshoot that might tweak this directory
            # so we allow this to be set
            install_scanner=[
                PathFinder(['/usr/bin'])
            ],
            opt_dirs=[
                '/opt/'
            ],
            script=None,
            subst_vars={
                'OBJCOPY': '${BINUTILS.INSTALL_ROOT}/objcopy',
                'AR': '${BINUTILS.INSTALL_ROOT}/ar',
            },
            shell_vars={'BINUTILS_INSTALL_ROOT': '${BINUTILS.INSTALL_ROOT}'},
            test_file='ld',
            opt_pattern=binutils_pattern
        )
    ]
)

binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'x86'), SystemPlatform('posix', 'x86_64')],
    targets=[SystemPlatform('posix', 'k1om')],
    info=[
        BinutilInfo(
            # standard location, however there might be
            # some posix offshoot that might tweak this directory
            # so we allow this to be set
            install_scanner=[
                PathFinder(['/usr/linux-k1om-4.7/bin'])
            ],
            opt_dirs=[],
            script=None,
            subst_vars={
                'OBJCOPY': '${BINUTILS.INSTALL_ROOT}/x86_64-k1om-linux-objcopy',
                'AR': '${BINUTILS.INSTALL_ROOT}/x86_64-k1om-linux-ar',
            },
            shell_vars={'BINUTILS_INSTALL_ROOT': '${BINUTILS.INSTALL_ROOT}'},
            test_file='x86_64-k1om-linux-ld',
            opt_pattern=binutils_pattern
        )
    ]
)

binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'ia64')],
    targets=[SystemPlatform('posix', 'ia64')],
    info=[
        BinutilInfo(
            # standard location, however there might be
            # some posix offshoot that might tweak this directory
            # so we allow this to be set
            install_scanner=[
                PathFinder(['/usr/bin'])
            ],
            opt_dirs=[
                '/opt/'
            ],
            script=None,
            subst_vars={
                'OBJCOPY': '${BINUTILS.INSTALL_ROOT}/objcopy',
                'AR': '${BINUTILS.INSTALL_ROOT}/ar',
            },
            shell_vars={'BINUTILS_INSTALL_ROOT': '${BINUTILS.INSTALL_ROOT}'},
            test_file='ld',
            opt_pattern=binutils_pattern
        )
    ]
)

binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add theh extra check for the stuff the need
    hosts=[SystemPlatform('cygwin', 'x86'), SystemPlatform('cygwin', 'x86_64')],
    targets=[SystemPlatform('cygwin', 'x86'), SystemPlatform('cygwin', 'x86_64')],
    info=[
        BinutilInfo(
            # standard location, however there might be
            # some posix offshoot that might tweak this directory
            # so we allow this to be set
            install_scanner=[
                PathFinder(['/usr/bin'])
            ],
            opt_dirs=[
                '/opt/'
            ],
            script=None,
            subst_vars={
                'OBJCOPY': '${BINUTILS.INSTALL_ROOT}/objcopy',
                'AR': '${BINUTILS.INSTALL_ROOT}/ar',
            },
            shell_vars={'BINUTILS_INSTALL_ROOT': '${BINUTILS.INSTALL_ROOT}'},
            test_file='ld',
            opt_pattern=binutils_pattern
        )
    ]
)

binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('cygwin', 'ia64')],
    targets=[SystemPlatform('cygwin', 'ia64')],
    info=[
        BinutilInfo(
            # standard location, however there might be
            # some posix offshoot that might tweak this directory
            # so we allow this to be set
            install_scanner=[
                PathFinder(['/usr/bin'])
            ],
            opt_dirs=[
                '/opt/'
            ],
            script=None,
            subst_vars={
                'OBJCOPY': '${BINUTILS.INSTALL_ROOT}/objcopy',
                'AR': '${BINUTILS.INSTALL_ROOT}/ar',
            },
            shell_vars={'BINUTILS_INSTALL_ROOT': '${BINUTILS.INSTALL_ROOT}'},
            test_file='ld',
            opt_pattern=binutils_pattern
        )
    ]
)

# mingw
binutils.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86'), SystemPlatform('win32', 'x86_64')],
    info=[
        BinutilInfo(
            install_scanner=[
                EnvFinder([
                    'MINGW_PREFIX',
                    'MINGW_PATH'
                ], 'bin'),
                PathFinder(['c:\\MinGW\\bin'])
            ],
            opt_dirs=[
                'c:\\MinGW\\opt\\'
            ],
            script=None,
            subst_vars={
                'ARCOM': '${TEMPFILE("$AR $ARFLAGS $TARGET $SOURCES",force_posix_paths=True)}',
                'LINKCOM': '${TEMPFILE("$LINK -o $TARGET $LINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS",force_posix_paths=True)}',
                'SHLINKCOM': '${TEMPFILE("$SHLINK -o $TARGET $SHLINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS",force_posix_paths=True)}',
                '__RPATH': '$_RPATH',
                'RPATHPREFIX': '-Wl,-rpath=',
            },
            shell_vars={'PATH': '${GCC.INSTALL_ROOT}'},
            test_file='ld.exe'
        )
    ]
)

# sunos
binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('sunos', 'any')],
    targets=[SystemPlatform('sunos', 'any')],
    info=[
        BinutilInfo(
            # standard location, however there might be
            # some posix offshoot that might tweak this directory
            # so we allow this to be set
            install_scanner=[
                PathFinder(['/usr/sfw/bin'])
            ],
            opt_dirs=[
                '/opt/'
            ],
            script=None,
            subst_vars={
                'OBJCOPY': '${BINUTILS.INSTALL_ROOT}/objcopy',
                'AR': '${BINUTILS.INSTALL_ROOT}/ar',
            },
            shell_vars={'BINUTILS_INSTALL_ROOT': '${BINUTILS.INSTALL_ROOT}'},
            test_file='ld',
            opt_pattern=binutils_pattern
        )
    ]
)

# mac
binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('darwin', 'any')],
    targets=[SystemPlatform('darwin', 'any')],
    info=[
        BinutilInfo(
            # standard location, however there might be
            # some posix offshoot that might tweak this directory
            # so we allow this to be set
            install_scanner=[
                PathFinder(['/usr/bin'])
            ],
            opt_dirs=[
                '/opt/'
            ],
            script=None,
            subst_vars={
                'OBJCOPY': '${BINUTILS.INSTALL_ROOT}/objcopy',
                'AR': '${BINUTILS.INSTALL_ROOT}/ar',
            },
            shell_vars={'BINUTILS_INSTALL_ROOT': '${BINUTILS.INSTALL_ROOT}'},
            test_file='ld',
            opt_pattern=binutils_pattern
        )
    ]
)

# android
# pre r8
binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('android', 'x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"], 'x86', 'i686-android-linux-', 'ld.exe'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}\platforms\android-${ANDROID_API}\arch-x86"',
                'OBJCOPY': r'i686-android-linux-objcopy.exe',
                'AR': r'i686-android-linux-ar.exe',
                'RANLIB': r'i686-android-linux-ranlib.exe',
                'AS': r'i686-android-linux-as.exe',
                'CHMODVALUE': None,

                'ARCOM': '${TEMPFILE("$AR $ARFLAGS $TARGET $SOURCES",force_posix_paths=True)}',
                'LINKCOM': '${TEMPFILE("$LINK -o $TARGET $LINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS",force_posix_paths=True)}',
                'SHLINKCOM': '${TEMPFILE("$SHLINK -o $TARGET $SHLINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS",force_posix_paths=True)}',
                '__RPATH': '$_RPATH',
                'RPATHPREFIX': '-Wl,-rpath=',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}\toolchains\x86-${BINUTILS.VERSION}\prebuilt\windows\bin'},
            test_file='i686-android-linux-ld.exe',

        )
    ]
)
# post r8
binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('android', 'x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"], 'x86', 'i686-linux-android-', 'ld.exe'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}\platforms\android-${ANDROID_API}\arch-x86"',
                'OBJCOPY': r'i686-linux-android-objcopy.exe',
                'AR': r'i686-linux-android-ar.exe',
                'RANLIB': r'i686-linux-android-ranlib.exe',
                'AS': r'i686-linux-android-as.exe',
                'CHMODVALUE': None,

                'ARCOM': '${TEMPFILE("$AR $ARFLAGS $TARGET $SOURCES",force_posix_paths=True)}',
                'LINKCOM': '${TEMPFILE("$LINK -o $TARGET $LINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS",force_posix_paths=True)}',
                'SHLINKCOM': '${TEMPFILE("$SHLINK -o $TARGET $SHLINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS",force_posix_paths=True)}',
                '__RPATH': '$_RPATH',
                'RPATHPREFIX': '-Wl,-rpath=',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}\toolchains\x86-${BINUTILS.VERSION}\prebuilt\windows\bin'},
            test_file='i686-linux-android-ld.exe',


        )
    ]
)


binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('android', 'x86_64')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"], 'x86', 'x86_64-linux-android-', 'ld.exe'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}\platforms\android-${ANDROID_API}\arch-x86_64"',
                'OBJCOPY': r'x86_64-linux-android-objcopy.exe',
                'AR': r'x86_64-linux-android-ar.exe',
                'RANLIB': r'x86_64-linux-android-ranlib.exe',
                'AS': r'x86_64-linux-android-as.exe',
                'CHMODVALUE': None,


                'ARCOM': '${TEMPFILE("$AR $ARFLAGS $TARGET $SOURCES",force_posix_paths=True)}',
                'LINKCOM': '${TEMPFILE("$LINK -o $TARGET $LINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS",force_posix_paths=True)}',
                'SHLINKCOM': '${TEMPFILE("$SHLINK -o $TARGET $SHLINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS",force_posix_paths=True)}',
                '__RPATH': '$_RPATH',
                'RPATHPREFIX': '-Wl,-rpath=',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}\toolchains\x86_64-${BINUTILS.VERSION}\prebuilt\windows-x86\bin'},
            test_file='x86_64-linux-android-ld.exe'
        )
    ]
)

binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('android', 'x86_64')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"], 'x86_64', 'x86_64-linux-android-', 'ld.exe'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}\platforms\android-${ANDROID_API}\arch-x86_64"',
                'OBJCOPY': r'x86_64-linux-android-objcopy.exe',
                'AR': r'x86_64-linux-android-ar.exe',
                'RANLIB': r'x86_64-linux-android-ranlib.exe',
                'AS': r'x86_64-linux-android-as.exe',
                'CHMODVALUE': None,

                'ARCOM': '${TEMPFILE("$AR $ARFLAGS $TARGET $SOURCES",force_posix_paths=True)}',
                'LINKCOM': '${TEMPFILE("$LINK -o $TARGET $LINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS",force_posix_paths=True)}',
                'SHLINKCOM': '${TEMPFILE("$SHLINK -o $TARGET $SHLINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS",force_posix_paths=True)}',
                '__RPATH': '$_RPATH',
                'RPATHPREFIX': '-Wl,-rpath=',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}\toolchains\x86_64-${BINUTILS.VERSION}\prebuilt\windows-x86_64\bin'},
            test_file='x86_64-linux-android-ld.exe'
        )
    ]
)

binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('android', 'arm')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"], 'arm', 'arm-linux-androideabi-', 'ld.exe'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}\platforms\android-${ANDROID_API}\arch-arm"',
                'OBJCOPY': r'arm-linux-androideabi-objcopy.exe',
                'AR': r'arm-linux-androideabi-ar.exe',
                'RANLIB': r'arm-linux-androideabi-ranlib.exe',
                'AS': r'arm-linux-androideabi-as.exe',
                'CHMODVALUE': None,

                'ARCOM': '${TEMPFILE("$AR $ARFLAGS $TARGET $SOURCES",force_posix_paths=True)}',
                'LINKCOM': '${TEMPFILE("$LINK -o $TARGET $LINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS",force_posix_paths=True)}',
                'SHLINKCOM': '${TEMPFILE("$SHLINK -o $TARGET $SHLINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS",force_posix_paths=True)}',
                '__RPATH': '$_RPATH',
                'RPATHPREFIX': '-Wl,-rpath=',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}\toolchains\arm-linux-androideabi-${BINUTILS.VERSION}\prebuilt\windows\bin'},
            test_file='arm-linux-androideabi-ld.exe',


        )
    ]
)

binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('android', 'x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"], 'x86', 'i686-linux-android-', 'ld.exe'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}\platforms\android-${ANDROID_API}\arch-x86"',
                'OBJCOPY': r'i686-linux-android-objcopy.exe',
                'AR': r'i686-linux-android-ar.exe',
                'RANLIB': r'i686-linux-android-ranlib.exe',
                'AS': r'i686-linux-android-as.exe',
                'CHMODVALUE': None,

                'ARCOM': '${TEMPFILE("$AR $ARFLAGS $TARGET $SOURCES",force_posix_paths=True)}',
                'LINKCOM': '${TEMPFILE("$LINK -o $TARGET $LINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS",force_posix_paths=True)}',
                'SHLINKCOM': '${TEMPFILE("$SHLINK -o $TARGET $SHLINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS",force_posix_paths=True)}',
                '__RPATH': '$_RPATH',
                'RPATHPREFIX': '-Wl,-rpath=',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}\toolchains\x86-${BINUTILS.VERSION}\prebuilt\windows-x86_64\bin'},
            test_file='i686-linux-android-ld.exe',


        )
    ]
)


binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('android', 'arm')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"], 'arm', 'arm-linux-androideabi-', 'ld.exe'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}\platforms\android-${ANDROID_API}\arch-arm"',
                'OBJCOPY': r'arm-linux-androideabi-objcopy.exe',
                'AR': r'arm-linux-androideabi-ar.exe',
                'RANLIB': r'arm-linux-androideabi-ranlib.exe',
                'AS': r'arm-linux-androideabi-as.exe',
                'CHMODVALUE': None,

                'ARCOM': '${TEMPFILE("$AR $ARFLAGS $TARGET $SOURCES",force_posix_paths=True)}',
                'LINKCOM': '${TEMPFILE("$LINK -o $TARGET $LINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS",force_posix_paths=True)}',
                'SHLINKCOM': '${TEMPFILE("$SHLINK -o $TARGET $SHLINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS",force_posix_paths=True)}',
                '__RPATH': '$_RPATH',
                'RPATHPREFIX': '-Wl,-rpath=',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}\toolchains\arm-linux-androideabi-${BINUTILS.VERSION}\prebuilt\windows-x86_64\bin'},
            test_file='arm-linux-androideabi-ld.exe',


        )
    ]
)

# pre r8
binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'any')],
    targets=[SystemPlatform('android', 'x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86', 'i686-android-linux-', 'ld'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86"',
                'OBJCOPY': r'i686-android-linux-objcopy',
                'AR': r'i686-android-linux-ar',
                'RANLIB': r'i686-android-linux-ranlib',
                'AS': r'i686-android-linux-as',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}/toolchains/x86-${BINUTILS.VERSION}/prebuilt/linux-x86/bin'},
            test_file='i686-android-linux-ld',

        )
    ]
)

# post r8
binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'any')],
    targets=[SystemPlatform('android', 'x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86', 'i686-linux-android-', 'ld'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86"',
                'OBJCOPY': r'i686-linux-android-objcopy',
                'AR': r'i686-linux-android-ar',
                'RANLIB': r'i686-linux-android-ranlib',
                'AS': r'i686-linux-android-as',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}/toolchains/x86-${BINUTILS.VERSION}/prebuilt/linux-x86/bin'},
            test_file='i686-linux-android-ld'
        )
    ]
)

binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'any')],
    targets=[SystemPlatform('android', 'arm')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'arm', 'arm-linux-androideabi-', 'ld'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-arm"',
                'OBJCOPY': r'arm-linux-androideabi-objcopy',
                'AR': r'arm-linux-androideabi-ar',
                'RANLIB': r'arm-linux-androideabi-ranlib',
                'AS': r'arm-linux-androideabi-as',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}/toolchains/arm-linux-androideabi-${BINUTILS.VERSION}/prebuilt/linux-x86/bin'},
            test_file='arm-linux-androideabi-ld'
        )
    ]
)

binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'x86_64')],
    targets=[SystemPlatform('android', 'x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86', 'i686-linux-android-', 'ld'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86"',
                'OBJCOPY': r'i686-linux-android-objcopy',
                'AR': r'i686-linux-android-ar',
                'RANLIB': r'i686-linux-android-ranlib',
                'AS': r'i686-linux-android-as',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}/toolchains/x86-${BINUTILS.VERSION}/prebuilt/linux-x86_64/bin'},
            test_file='i686-linux-android-ld'
        )
    ]
)

binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'any')],
    targets=[SystemPlatform('android', 'x86_64')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86', 'x86_64-linux-android-', 'ld'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86_64"',
                'OBJCOPY': r'x86_64-linux-android-objcopy',
                'AR': r'x86_64-linux-android-ar',
                'RANLIB': r'x86_64-linux-android-ranlib',
                'AS': r'x86_64-linux-android-as',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}/toolchains/x86_64-${BINUTILS.VERSION}/prebuilt/linux-x86/bin'},
            test_file='x86_64-linux-android-ld'
        )
    ]
)

binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'x86_64')],
    targets=[SystemPlatform('android', 'x86_64')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86_64', 'x86_64-linux-android-', 'ld'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86_64"',
                'OBJCOPY': r'x86_64-linux-android-objcopy',
                'AR': r'x86_64-linux-android-ar',
                'RANLIB': r'x86_64-linux-android-ranlib',
                'AS': r'x86_64-linux-android-as',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}/toolchains/x86_64-${BINUTILS.VERSION}/prebuilt/linux-x86_64/bin'},
            test_file='x86_64-linux-android-ld'
        )
    ]
)


binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'any')],
    targets=[SystemPlatform('android', 'arm')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'arm', 'arm-linux-androideabi-', 'ld'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-arm"',
                'OBJCOPY': r'arm-linux-androideabi-objcopy',
                'AR': r'arm-linux-androideabi-ar',
                'RANLIB': r'arm-linux-androideabi-ranlib',
                'AS': r'arm-linux-androideabi-as',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}/toolchains/arm-linux-androideabi-${BINUTILS.VERSION}/prebuilt/linux-x86_64/bin'},
            test_file='arm-linux-androideabi-ld'
        )
    ]
)

# mac (darwin) post r8
binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('darwin', 'any')],
    targets=[SystemPlatform('android', 'x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86', 'i686-linux-android-', 'ld'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86"',
                'OBJCOPY': r'i686-linux-android-objcopy',
                'AR': r'i686-linux-android-ar',
                'RANLIB': r'i686-linux-android-ranlib',
                'AS': r'i686-linux-android-as',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}/toolchains/x86-${BINUTILS.VERSION}/prebuilt/darwin-x86/bin'},
            test_file='i686-linux-android-ld'
        )
    ]
)

binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('darwin', 'any')],
    targets=[SystemPlatform('android', 'arm')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'arm', 'arm-linux-androideabi-', 'ld'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-arm"',
                'OBJCOPY': r'arm-linux-androideabi-objcopy',
                'AR': r'arm-linux-androideabi-ar',
                'RANLIB': r'arm-linux-androideabi-ranlib',
                'AS': r'arm-linux-androideabi-as',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}/toolchains/arm-linux-androideabi-${BINUTILS.VERSION}/prebuilt/darwin-x86/bin'},
            test_file='arm-linux-androideabi-ld'
        )
    ]
)

binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('darwin', 'x86_64')],
    targets=[SystemPlatform('android', 'x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86', 'i686-linux-android-', 'ld'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86"',
                'OBJCOPY': r'i686-linux-android-objcopy',
                'AR': r'i686-linux-android-ar',
                'RANLIB': r'i686-linux-android-ranlib',
                'AS': r'i686-linux-android-as',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}/toolchains/x86-${BINUTILS.VERSION}/prebuilt/darwin-x86_64/bin'},
            test_file='i686-linux-android-ld'
        )
    ]
)

binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('darwin', 'any')],
    targets=[SystemPlatform('android', 'x86_64')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86', 'x86_64-linux-android-', 'ld'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86_64"',
                'OBJCOPY': r'x86_64-linux-android-objcopy',
                'AR': r'x86_64-linux-android-ar',
                'RANLIB': r'x86_64-linux-android-ranlib',
                'AS': r'x86_64-linux-android-as',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}/toolchains/x86_64-${BINUTILS.VERSION}/prebuilt/darwin-x86/bin'},
            test_file='x86_64-linux-android-ld'
        )
    ]
)

binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('darwin', 'x86_64')],
    targets=[SystemPlatform('android', 'x86_64')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86_64', 'x86_64-linux-android-', 'ld'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86_64"',
                'OBJCOPY': r'x86_64-linux-android-objcopy',
                'AR': r'x86_64-linux-android-ar',
                'RANLIB': r'x86_64-linux-android-ranlib',
                'AS': r'x86_64-linux-android-as',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}/toolchains/x86_64-${BINUTILS.VERSION}/prebuilt/darwin-x86_64/bin'},
            test_file='x86_64-linux-android-ld'
        )
    ]
)


binutils.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('darwin', 'any')],
    targets=[SystemPlatform('android', 'arm')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'arm', 'arm-linux-androideabi-', 'ld'),
            script=None,
            subst_vars={
                'SYS_ROOT': r'"${BINUTILS.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-arm"',
                'OBJCOPY': r'arm-linux-androideabi-objcopy',
                'AR': r'arm-linux-androideabi-ar',
                'RANLIB': r'arm-linux-androideabi-ranlib',
                'AS': r'arm-linux-androideabi-as',
            },
            shell_vars={'PATH': r'${BINUTILS.INSTALL_ROOT}/toolchains/arm-linux-androideabi-${BINUTILS.VERSION}/prebuilt/darwin-x86_64/bin'},
            test_file='arm-linux-androideabi-ld'
        )
    ]
)


binutils.Register(
    hosts=[SystemPlatform('posix', 'x86_64')],
    targets=[SystemPlatform('freebsd', 'x86_64')],
    info=[
        BinutilInfo(
            # standard location, however there might be
            # some posix offshoot that might tweak this directory
            # so we allow this to be set
            install_scanner=[PathFinder(['/usr/bin'])],
            opt_dirs=['/opt/'],
            opt_pattern=r'gcc-((\d+\.)*\d+)-crossfreebsd',
            script=None,
            subst_vars={
                'OBJCOPY': 'x86_64-unknown-freebsd10.0-objcopy',
                'AR': 'x86_64-unknown-freebsd10.0-ar',
            },
            shell_vars={'PATH': '${BINUTILS.INSTALL_ROOT}'},
            test_file='x86_64-unknown-freebsd10.0-ld',
        )
    ]
)

# vim: set et ts=4 sw=4 ai :
