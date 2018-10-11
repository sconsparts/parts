import os
from common import gcc, GnuInfo
from parts.tools.Common.Finders import PathFinder, ScriptFinder, EnvFinder
from parts.platform_info import SystemPlatform
from parts.tools.Common.ToolInfo import ToolInfo
import android

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'x86'), SystemPlatform('posix', 'x86_64'), SystemPlatform('freebsd', 'x86_64')],
    targets=[SystemPlatform('posix', 'x86'), SystemPlatform('posix', 'x86_64'), SystemPlatform('freebsd', 'x86_64')],
    info=[
        GnuInfo(
            # standard location, however there might be
            # some posix offshoot that might tweak this directory
            # so we allow this to be set
            install_scanner=[
                PathFinder(['/usr/bin'])
            ],
            opt_dirs=[
                '/opt/'
            ]+['/opt/rh/devtoolset-{0}/root/usr/bin/'.format(i) for i in range(3, 10)],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${GCC.INSTALL_ROOT}'},
            test_file='gcc'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'ia64')],
    targets=[SystemPlatform('posix', 'ia64')],
    info=[
        GnuInfo(
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
            subst_vars={},
            shell_vars={'PATH': '${GCC.INSTALL_ROOT}'},
            test_file='gcc'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'any')],
    targets=[SystemPlatform('posix', 'k1om')],
    info=[
        GnuInfo(
            # standard location, however there might be
            # some posix offshoot that might tweak this directory
            # so we allow this to be set
            install_scanner=[
                PathFinder(['/usr/linux-k1om-4.7/bin'])
            ],
            opt_dirs=[
                #'/opt/'
            ],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${GCC.INSTALL_ROOT}'},
            test_file='x86_64-k1om-linux-gcc'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add theh extra check for the stuff the need
    hosts=[SystemPlatform('cygwin', 'x86'), SystemPlatform('cygwin', 'x86_64')],
    targets=[SystemPlatform('cygwin', 'x86'), SystemPlatform('cygwin', 'x86_64')],
    info=[
        GnuInfo(
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
            subst_vars={},
            shell_vars={'PATH': '${GCC.INSTALL_ROOT}'},
            test_file='gcc'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('cygwin', 'ia64')],
    targets=[SystemPlatform('cygwin', 'ia64')],
    info=[
        GnuInfo(
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
            subst_vars={},
            shell_vars={'PATH': '${GCC.INSTALL_ROOT}'},
            test_file='gcc'
        )
    ]
)

# sunos
gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('sunos', 'any')],
    targets=[SystemPlatform('sunos', 'any')],
    info=[
        GnuInfo(
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
            subst_vars={},
            shell_vars={'PATH': '${GCC.INSTALL_ROOT}'},
            test_file='gcc'
        )
    ]
)

# mac
gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('darwin', 'any')],
    targets=[SystemPlatform('darwin', 'any')],
    info=[
        GnuInfo(
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
            subst_vars={},
            shell_vars={'PATH': '${GCC.INSTALL_ROOT}'},
            test_file='gcc'
        )
    ]
)

# android pre r8
gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('android', 'x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"], 'x86', 'i686-android-linux-', 'gcc.exe'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}\platforms\android-${ANDROID_API}\arch-x86"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}\toolchains\x86-${GCC.VERSION}\prebuilt\windows\bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}\toolchains\x86-${GCC.VERSION}\prebuilt\windows\include'
            },
            test_file='i686-android-linux-gcc.exe'
        )
    ]
)

# post r8
gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('android', 'x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"], 'x86', 'i686-linux-android-', 'gcc.exe'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}\platforms\android-${ANDROID_API}\arch-x86"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}\toolchains\x86-${GCC.VERSION}\prebuilt\windows\bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}\toolchains\x86-${GCC.VERSION}\prebuilt\windows\include'
            },
            test_file='i686-linux-android-gcc.exe'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('android', 'x86_64')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"], 'x86', 'x86_64-linux-android-', 'gcc.exe'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}\platforms\android-${ANDROID_API}\arch-x86_64"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}\toolchains\x86_64-${GCC.VERSION}\prebuilt\windows-x86\bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}\toolchains\x86_64-${GCC.VERSION}\prebuilt\windows-x86\include'
            },
            test_file='x86_64-linux-android-gcc.exe'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('android', 'x86_64')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"], 'x86_64', 'x86_64-linux-android-', 'gcc.exe'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}\platforms\android-${ANDROID_API}\arch-x86_64"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}\toolchains\x86_64-${GCC.VERSION}\prebuilt\windows-x86_64\bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}\toolchains\x86_64-${GCC.VERSION}\prebuilt\windows-x86_64\include'
            },
            test_file='x86_64-linux-android-gcc.exe'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('android', 'arm')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"], 'arm', 'arm-linux-androideabi-', 'gcc.exe'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}\platforms\android-${ANDROID_API}\arch-arm"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}\toolchains\arm-linux-androideabi-${GCC.VERSION}\prebuilt\windows\bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}\toolchains\arm-linux-androideabi-${GCC.VERSION}\prebuilt\windows\include'
            },
            test_file='arm-linux-androideabi-gcc.exe'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('android', 'x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"], 'x86', 'i686-linux-android-', 'gcc.exe'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}\platforms\android-${ANDROID_API}\arch-x86"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}\toolchains\x86-${GCC.VERSION}\prebuilt\windows-x86_64\bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}\toolchains\x86-${GCC.VERSION}\prebuilt\windows-x86_64\include'
            },
            test_file='i686-linux-android-gcc.exe'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('android', 'arm')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"], 'arm', 'arm-linux-androideabi-', 'gcc.exe'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}\platforms\android-${ANDROID_API}\arch-arm"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}\toolchains\arm-linux-androideabi-${GCC.VERSION}\prebuilt\windows-x86_64\bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}\toolchains\arm-linux-androideabi-${GCC.VERSION}\prebuilt\windows-x86_64\include'
            },
            test_file='arm-linux-androideabi-gcc.exe'
        )
    ]
)

# pre r8
gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'any')],
    targets=[SystemPlatform('android', 'x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86', 'i686-android-linux-', 'gcc'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86-${GCC.VERSION}/prebuilt/linux-x86/bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86-${GCC.VERSION}/prebuilt/linux-x86/include'
            },
            test_file='i686-android-linux-gcc'
        )
    ]
)
# posix
# post r8
gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'any')],
    targets=[SystemPlatform('android', 'x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86', 'i686-linux-android-', 'gcc'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86-${GCC.VERSION}/prebuilt/linux-x86/bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86-${GCC.VERSION}/prebuilt/linux-x86/include'
            },
            test_file='i686-linux-android-gcc'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'any')],
    targets=[SystemPlatform('android', 'arm')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'arm', 'arm-linux-androideabi-', 'gcc'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-arm"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}/toolchains/arm-linux-androideabi-${GCC.VERSION}/prebuilt/linux-x86/bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}/toolchains/arm-linux-androideabi-${GCC.VERSION}/prebuilt/linux-x86/include'
            },
            test_file='arm-linux-androideabi-gcc'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'x86_64')],
    targets=[SystemPlatform('android', 'x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86', 'i686-linux-android-', 'gcc'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86-${GCC.VERSION}/prebuilt/linux-x86_64/bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86-${GCC.VERSION}/prebuilt/linux-x86_64/include'
            },
            test_file='i686-linux-android-gcc'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'any')],
    targets=[SystemPlatform('android', 'x86_64')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86', 'x86_64-linux-android-', 'gcc'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86_64"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86_64-${GCC.VERSION}/prebuilt/linux-x86/bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86_64-${GCC.VERSION}/prebuilt/linux-x86/include'
            },
            test_file='x86_64-linux-android-gcc'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'x86_64')],
    targets=[SystemPlatform('android', 'x86_64')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86_64', 'x86_64-linux-android-', 'gcc'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86_64"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86_64-${GCC.VERSION}/prebuilt/linux-x86_64/bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86_64-${GCC.VERSION}/prebuilt/linux-x86_64/include'
            },
            test_file='x86_64-linux-android-gcc'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'x86_64')],
    targets=[SystemPlatform('android', 'arm')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'arm', 'arm-linux-androideabi-', 'gcc'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-arm"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}/toolchains/arm-linux-androideabi-${GCC.VERSION}/prebuilt/linux-x86_64/bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}/toolchains/arm-linux-androideabi-${GCC.VERSION}/prebuilt/linux-x86_64/include'
            },
            test_file='arm-linux-androideabi-gcc'
        )
    ]
)

# mac
# post r8
gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('darwin', 'any')],
    targets=[SystemPlatform('android', 'x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86', 'i686-linux-android-', 'gcc'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86-${GCC.VERSION}/prebuilt/darwin-x86/bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86-${GCC.VERSION}/prebuilt/darwin-x86/include'
            },
            test_file='i686-linux-android-gcc'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('darwin', 'any')],
    targets=[SystemPlatform('android', 'arm')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'arm', 'arm-linux-androideabi-', 'gcc'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-arm"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}/toolchains/arm-linux-androideabi-${GCC.VERSION}/prebuilt/darwin-x86/bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}/toolchains/arm-linux-androideabi-${GCC.VERSION}/prebuilt/darwin-x86/include'
            },
            test_file='arm-linux-androideabi-gcc'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('darwin', 'x86_64')],
    targets=[SystemPlatform('android', 'x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86', 'i686-linux-android-', 'gcc'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86-${GCC.VERSION}/prebuilt/darwin-x86_64/bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86-${GCC.VERSION}/prebuilt/darwin-x86_64/include'
            },
            test_file='i686-linux-android-gcc'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('darwin', 'any')],
    targets=[SystemPlatform('android', 'x86_64')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86', 'x86_64-linux-android-', 'gcc'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86_64"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86_64-${GCC.VERSION}/prebuilt/darwin-x86/bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86_64-${GCC.VERSION}/prebuilt/darwin-x86/include'
            },
            test_file='x86_64-linux-android-gcc'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('darwin', 'x86_64')],
    targets=[SystemPlatform('android', 'x86_64')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'x86_64', 'x86_64-linux-android-', 'gcc'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-x86_64"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86_64-${GCC.VERSION}/prebuilt/darwin-x86_64/bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}/toolchains/x86_64-${GCC.VERSION}/prebuilt/darwin-x86_64/include'
            },
            test_file='x86_64-linux-android-gcc'
        )
    ]
)

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('darwin', 'x86_64')],
    targets=[SystemPlatform('android', 'arm')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"], 'arm', 'arm-linux-androideabi-', 'gcc'),
            script=None,
            subst_vars={'SYS_ROOT': r'"${GCC.INSTALL_ROOT}/platforms/android-${ANDROID_API}/arch-arm"'},
            shell_vars={
                'PATH': r'${GCC.INSTALL_ROOT}/toolchains/arm-linux-androideabi-${GCC.VERSION}/prebuilt/darwin-x86_64/bin',
                        'C_INCLUDE_PATH': r'${GCC.INSTALL_ROOT}/toolchains/arm-linux-androideabi-${GCC.VERSION}/prebuilt/darwin-x86_64/include'
            },
            test_file='arm-linux-androideabi-gcc'
        )
    ]
)

# MINGW compiler on windows

gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'x86'), SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('win32', 'x86'), SystemPlatform('win32', 'x86_64')],
    info=[
        GnuInfo(
            # standard location, however there might be
            # some posix offshoot that might tweak this directory
            # so we allow this to be set
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
            subst_vars={},
            shell_vars={'PATH': '${GCC.INSTALL_ROOT}'},
            test_file='gcc.exe'
        )
    ]
)

# FreeBSD-target on POSIX host
gcc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'x86_64')],
    targets=[SystemPlatform('freebsd', 'x86_64')],
    info=[
        GnuInfo(
            # standard location, however there might be
            # some posix offshoot that might tweak this directory
            # so we allow this to be set
            install_scanner=[PathFinder(['/usr/bin'])],
            opt_dirs=['/opt/'],
            opt_pattern=r'gcc-((\d+\.)*\d+)-crossfreebsd',
            script=None,
            subst_vars={'APPENDS': {
                'LIBPATH': [r'${GCC.INSTALL_ROOT}/../x86_64-unknown-freebsd10.0/usr/local/lib',
                            r'${GCC.INSTALL_ROOT}/../x86_64-unknown-freebsd10.0/usr/local/lib/gcc44',
                            r'/usr/local/lib',
                            r'/usr/local/lib/gcc44'],
                'CPPPATH': [r'${GCC.INSTALL_ROOT}/../x86_64-unknown-freebsd10.0/usr/local/lib/gcc44/include/c++',
                            r'${GCC.INSTALL_ROOT}/../x86_64-unknown-freebsd10.0/usr/local/lib/gcc44/include/c++/x86_64-portbld-freebsd10.0',
                            r'/usr/local/lib/gcc44/include/c++',
                            r'/usr/local/lib/gcc44/include/c++/x86_64-portbld-freebsd10.0', ]},
                        },
            shell_vars={'PATH': '${GCC.INSTALL_ROOT}'},
            test_file='x86_64-unknown-freebsd10.0-gcc'
        )
    ]
)
