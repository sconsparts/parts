from __future__ import absolute_import, division, print_function

import os

from parts.platform_info import SystemPlatform
from parts.tools.Common.Finders import (EnvFinder, PathFinder, RegFinder,
                                        ScriptFinder)
from parts.tools.Common.ToolInfo import ToolInfo

from . import regscanner
from .common import Intelc, IntelcInfo

# composer (mainstream)
# 32-bit 12.1
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        IntelcInfo(
            version='12.1.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\2.1',
                 r'Software\Intel\Suites\2.1'],
                r'\Defaults\C++\IA32',
                'ICPP_COMPOSER2011'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\ia32\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/ia32/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit 12.1 64-bit
Intelc.Register(
    hosts=[SystemPlatform('win32', 'x86')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='12.1.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\2.1',
                 r'Software\Intel\Suites\2.1'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPOSER2011'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32_intel64/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32_intel64/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\intel64\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)

# Composer XE
# 32-bit 12.1
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        IntelcInfo(
            version='12.1.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\12.1',
                 r'Software\Intel\Suites\12.1'],
                r'\Defaults\C++\IA32',
                'ICPP_COMPOSER2011'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\ia32\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/ia32/'
            },
            test_file='icl.exe'
        )
    ]
)

# 32-bit 12.1 64-bit-cross
Intelc.Register(
    hosts=[SystemPlatform('win32', 'x86')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='12.1.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\12.1',
                 r'Software\Intel\Suites\12.1'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPILER12'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32_intel64/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32_intel64/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\intel64\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit 12.1 64-bit
Intelc.Register(
    hosts=[SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='12.1.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\12.1',
                 r'Software\Intel\Suites\12.1'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPILER12'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/intel64/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/intel64/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\intel64\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)


# composer (mainstream)
# 32-bit 12.0
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        IntelcInfo(
            version='12.0.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\2.0',
                 r'Software\Intel\Suites\2.0'],
                r'\Defaults\C++\IA32',
                'ICPP_COMPOSER2011'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32/',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/ia32/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit 12.0 64-bit
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='12.0.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\2.0',
                 r'Software\Intel\Suites\2.0'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPOSER2011'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32_intel64/',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)

# Composer XE
# 32-bit 12.0
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        IntelcInfo(
            version='12.0.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\12.0',
                 r'Software\Intel\Suites\12.0'],
                r'\Defaults\C++\IA32',
                'ICPP_COMPOSER2011'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32/',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/ia32/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit 12.0 64-bit-cross
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='12.0.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\12.0',
                 r'Software\Intel\Suites\12.0'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPILER12'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32_intel64/',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit 12.0 64-bit
Intelc.Register(
    hosts=[SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='12.0.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\12.0',
                 r'Software\Intel\Suites\12.0'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPILER12'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/intel64/',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit 13.* 64-bit
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='13.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\2.0',
                 r'Software\Intel\Suites\2.0'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPOSER2013'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32_intel64/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\intel64\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)

# Composer XE
# 32-bit 13.*
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        IntelcInfo(
            version='13.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\13.0',
                 r'Software\Intel\Suites\13.0'],
                r'\Defaults\C++\IA32',
                'ICPP_COMPOSER2013'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\intel64\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/ia32/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit 13.* 64-bit-cross
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='13.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\13.0',
                 r'Software\Intel\Suites\13.0'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPILER13'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32_intel64/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\intel64\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit 13.* 64-bit
Intelc.Register(
    hosts=[SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='13.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\13.0',
                 r'Software\Intel\Suites\13.0'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPILER13'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/intel64/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\intel64\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)

# 14.* starts here
Intelc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('posix', 'k1om')],
    info=[
        IntelcInfo(
            version='14.*',  # this is just a place holder for this "beta" stuff until it is better defined
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\14.0',
                 r'Software\Intel\Suites\14.0'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPILER14'),
            script=None,
            subst_vars={},
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/intel64_mic/',
                'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/mic/',
                'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/mic/'
            },
            test_file='icc.exe'
        )
    ]
)

# Intel Composer 14 for Windows starts here
# Composer XE
# 32-bit 14.*
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        IntelcInfo(
            version='14.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\14.0',
                 r'Software\Intel\Suites\14.0'],
                r'\Defaults\C++\IA32',
                'ICPP_COMPILER14'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\ia32\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/ia32/'
            },
            test_file='icl.exe'
        )
    ]
)

# 32-bit 14.1 64-bit-cross
Intelc.Register(
    hosts=[SystemPlatform('win32', 'x86')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='14.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\14.0',
                 r'Software\Intel\Suites\14.0'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPILER14'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32_intel64/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32_intel64/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\intel64\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit 14.1 64-bit
Intelc.Register(
    hosts=[SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='14.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\14.0',
                 r'Software\Intel\Suites\14.0'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPILER14'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/intel64/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/intel64/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\intel64\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)
# 15.* starts here
Intelc.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('posix', 'k1om')],
    info=[
        IntelcInfo(
            version='15.*',  # this is just a place holder for this "beta" stuff until it is better defined
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\15.0',
                 r'Software\Intel\Suites\15.0'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPILER15'),
            script=None,
            subst_vars={},
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/intel64_mic/',
                'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/mic/',
                'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/mic/'
            },
            test_file='icc.exe'
        )
    ]
)

# Intel Composer 15 for Windows starts here
# Composer XE
# 32-bit native 15.*
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        IntelcInfo(
            version='15.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\15.0',
                 r'Software\Intel\Suites\15.0'],
                r'\Defaults\C++\IA32',
                'ICPP_COMPILER15'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\ia32\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/ia32/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit cross
Intelc.Register(
    hosts=[SystemPlatform('win32', 'x86')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='15.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\15.0',
                 r'Software\Intel\Suites\15.0'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPILER15'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32_intel64/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32_intel64/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\intel64\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit native
Intelc.Register(
    hosts=[SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='15.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\15.0',
                 r'Software\Intel\Suites\15.0'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPILER15'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/intel64/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/intel64/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\intel64\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)


# Intel Composer 16 for Windows starts here
# Composer XE
# 32-bit native 16.*
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        IntelcInfo(
            version='16.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\16.0',
                 r'Software\Intel\Suites\16.0'],
                r'\Defaults\C++\IA32',
                'ICPP_COMPILER16'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\ia32\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/ia32/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit cross
Intelc.Register(
    hosts=[SystemPlatform('win32', 'x86')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='16.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\16.0',
                 r'Software\Intel\Suites\16.0'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPILER16'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32_intel64/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32_intel64/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\intel64\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit native
Intelc.Register(
    hosts=[SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='16.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\16.0',
                 r'Software\Intel\Suites\16.0'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPILER16'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/intel64/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/intel64/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\intel64\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)

# Intel Composer 17 for Windows starts here
# Composer XE
# 32-bit native 17.*
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        IntelcInfo(
            version='17.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\17.0',
                 r'Software\Intel\Suites\17.0'],
                r'\Defaults\C++\IA32',
                'ICPP_COMPILER17'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\ia32\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/ia32/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit cross
Intelc.Register(
    hosts=[SystemPlatform('win32', 'x86')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='17.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\17.0',
                 r'Software\Intel\Suites\17.0'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPILER17'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32_intel64/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32_intel64/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\intel64\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit native
Intelc.Register(
    hosts=[SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='17.*',
            install_scanner=regscanner.reg_scanner_v12(
                [r'Software\Wow6432Node\Intel\Suites\17.0',
                 r'Software\Intel\Suites\17.0'],
                r'\Defaults\C++\EM64T',
                'ICPP_COMPILER17'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/intel64/compilervars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/intel64/' + os.pathsep +
                        r'C:\Program Files${" (x86)" if HOST_ARCH=="x86_64" else ""}\Common Files\Intel\Shared Libraries\redist\intel64\compiler',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/compiler/lib/intel64/'
            },
            test_file='icl.exe'
        )
    ]
)
