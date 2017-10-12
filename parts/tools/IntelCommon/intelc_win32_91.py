from common import Intelc
from parts.tools.Common.ToolInfo import ToolInfo
from parts.tools.Common.Finders import RegFinder, EnvFinder, PathFinder, ScriptFinder
from parts.platform_info import SystemPlatform
import os

# 32-bit 9.1
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        ToolInfo(
            version='9.1',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Intel\Compilers\91\IA32\ProductDir',
                    r'Software\Intel\Compilers\91\IA32\ProductDir'
                ]),
                EnvFinder([
                    'ICPP_COMPILER91'
                ], './IA32'),
                PathFinder([
                    r'C:\Program Files (x86)\Intel\Compiler\C++\9.1\IA32',
                    r'C:\Program Files\Intel\Compiler\C++\9.1\IA32'
                ])
            ],
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

# 64-bit cross
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        ToolInfo(
            version='9.1',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Intel\Compilers\91\EM64T\ProductDir',
                    r'Software\Intel\Compilers\91\EM64T\ProductDir'
                ]),
                EnvFinder([
                    'ICPP_COMPILER91'
                ], './EM64T'),
                PathFinder([
                    r'C:\Program Files (x86)\Intel\Compiler\C++\9.1\EM64T',
                    r'C:\Program Files\Intel\Compiler\C++\9.1\EM64T'
                ])
            ],
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

# 64-bit-ia64 cross
Intelc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'ia64')],
    info=[
        ToolInfo(
            version='9.1',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Intel\Compilers\91\Itanium\ProductDir',
                    r'Software\Intel\Compilers\91\Itanium\ProductDir'
                ]),
                EnvFinder([
                    'ICPP_COMPILER91'
                ], './Itanium'),
                PathFinder([
                    r'C:\Program Files (x86)\Intel\Compiler\C++\9.1\Itanium',
                    r'C:\Program Files\Intel\Compiler\C++\9.1\Itanium'
                ])
            ],
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
