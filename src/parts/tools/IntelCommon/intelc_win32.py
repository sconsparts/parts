from __future__ import absolute_import, division, print_function

import os

from parts.platform_info import SystemPlatform
from parts.tools.Common.Finders import (EnvFinder, PathFinder, RegFinder,
                                        ScriptFinder)

from . import common, regscanner
from .common import Intelc, IntelcInfo

# 32-bit 11.1 ( composer mainstream)
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        IntelcInfo(
            version='11,11.1.*',
            install_scanner=regscanner.reg_scanner2(
                [r'Software\Wow6432Node\Intel\Suites\1.0',
                 r'Software\Intel\Suites\1.0'],
                common.intel_11_1,
                'ia32',
                'ICPP_COMPILER11', '11.1'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/iclvars_ia32.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32/',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/lib/ia32/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit 11.1 ( composer mainstream )
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='11,11.1.*',
            install_scanner=regscanner.reg_scanner2(
                [r'Software\Wow6432Node\Intel\Suites\1.0',
                 r'Software\Intel\Suites\1.0'],
                common.intel_11_1,
                'EM64T',
                'ICPP_COMPILER11', '11.1'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/IA32_Intel64/iclvars_IA32_intel64.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/IA32_Intel64/',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/lib/intel64'
            },
            test_file='icl.exe'
        )
    ]
)

# 32-bit 11.1 ( pro )
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        IntelcInfo(
            version='11,11.1.*',
            install_scanner=regscanner.reg_scanner2(
                [r'Software\Wow6432Node\Intel\Suites\11.1',
                 r'Software\Intel\Suites\11.1'],
                common.intel_11_1,
                'ia32',
                'ICPP_COMPILER11', '11.1'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/iclvars_ia32.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32/',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/lib/ia32/'
            },
            test_file='icl.exe'
        )
    ]
)


# 64-bit 11.1 ( Pro cross)
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='11,11.1.*',
            install_scanner=regscanner.reg_scanner2(
                [r'Software\Wow6432Node\Intel\Suites\11.1',
                 r'Software\Intel\Suites\11.1'],
                common.intel_11_1,
                'EM64T',
                'ICPP_COMPILER11', '11.1'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32_Intel64/iclvars_IA32_intel64.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32_intel64/',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/lib/intel64'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit 11.1 ( Pro native)
Intelc.Register(
    hosts=[SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='11,11.1.*',
            install_scanner=regscanner.reg_scanner2(
                [r'Software\Wow6432Node\Intel\Suites\11.1'],
                common.intel_11_1,
                'EM64T_NATIVE',
                'ICPP_COMPILER11', '11.1'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/Intel64/iclvars_intel64.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/Intel64/',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/lib/intel64'
            },
            test_file='icl.exe'
        )
    ]
)


# ia64-bit 11.1 ( pro cross)
Intelc.Register(
    hosts=[SystemPlatform('win32', 'x86'), SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('win32', 'ia64')],
    info=[
        IntelcInfo(
            version='11,11.1.*',
            install_scanner=regscanner.reg_scanner2(
                [r'Software\Wow6432Node\Intel\Suites\11.1',
                 r'Software\Intel\Suites\11.1'],
                common.intel_11_1,
                'Itanium',
                'ICPP_COMPILER11', '11.1'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/IA32_ia64/iclvars_ia32_ia64.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/IA32_ia64/',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/lib/ia64'
            },
            test_file='icl.exe'
        )
    ]
)

# 32-bit 11.0
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        IntelcInfo(
            version='11.0.*',
            install_scanner=regscanner.reg_scanner(
                [r'Software\Wow6432Node\Intel\Compilers\C++',
                 r'Software\Intel\Compilers\C++'],
                common.intel_11,
                'ia32',
                'ICPP_COMPILER11', '11'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/iclvars_ia32.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/lib/ia32'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit cross 11.x
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='11.0.*',
            install_scanner=regscanner.reg_scanner(
                [r'Software\Wow6432Node\Intel\Compilers\C++',
                 r'Software\Intel\Compilers\C++'],
                common.intel_11,
                'EM64T',
                'ICPP_COMPILER11', '11'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32_intel64/iclvars_ia32_intel64.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/ia32_intel64',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/lib/ia32_intel64'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit native 11.x
Intelc.Register(
    hosts=[SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='11.0.*',
            install_scanner=regscanner.reg_scanner(
                [r'Software\Wow6432Node\Intel\Compilers\C++',
                 r'Software\Intel\Compilers\C++'],
                common.intel_11,
                'EM64T_NATIVE',
                'ICPP_COMPILER11', '11'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/intel64/iclvars_intel64.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/intel64',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/lib/intel64'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit ia64 11.x
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'ia64')],
    info=[
        IntelcInfo(
            version='11.0.*',
            install_scanner=regscanner.reg_scanner(
                [r'Software\Wow6432Node\Intel\Compilers\C++',
                 r'Software\Intel\Compilers\C++'],
                common.intel_11,
                'Itanium',  # double check this value
                'ICPP_COMPILER11', '11'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ICLVars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/Itanium',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/lib/Itanium'
            },
            test_file='icl.exe'
        )
    ]
)

# 32-bit 10.x
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        IntelcInfo(
            version='10.*',
            install_scanner=regscanner.reg_scanner(
                [r'Software\Wow6432Node\Intel\Compilers\C++',
                 r'Software\Intel\Compilers\C++'],
                common.intel_10,
                'IA32',
                'ICPP_COMPILER10', '10'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ICLVars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/lib/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit 10.x
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        IntelcInfo(
            version='10.*',
            install_scanner=regscanner.reg_scanner(
                [r'Software\Wow6432Node\Intel\Compilers\C++',
                 r'Software\Intel\Compilers\C++'],
                common.intel_10,
                'EM64T',
                'ICPP_COMPILER10', '10'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ICLVars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/lib/'
            },
            test_file='icl.exe'
        )
    ]
)

# 64-bit ia64 10.x
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'ia64')],
    info=[
        IntelcInfo(
            version='10.*',
            install_scanner=regscanner.reg_scanner(
                [r'Software\Wow6432Node\Intel\Compilers\C++',
                 r'Software\Intel\Compilers\C++'],
                common.intel_10,
                'Itanium',
                'ICPP_COMPILER10', '10'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ICLVars.bat'),
            subst_vars={

            },
            shell_vars={
                'PATH': '${INTELC.INSTALL_ROOT}/bin/',
                        'INCLUDE': '${INTELC.INSTALL_ROOT}/include/',
                        'LIB': '${INTELC.INSTALL_ROOT}/lib/'
            },
            test_file='icl.exe'
        )
    ]
)
