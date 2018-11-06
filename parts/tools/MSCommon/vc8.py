# version 8 2005
from __future__ import absolute_import, division, print_function

import os

from parts.platform_info import SystemPlatform
from parts.tools.Common.Finders import (EnvFinder, PathFinder, RegFinder,
                                        ScriptFinder)
from parts.tools.Common.ToolInfo import ToolInfo

import SCons.Platform
from .common import framework_root, framework_root64, msvc

# 32-bit
msvc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        ToolInfo(
            version='8.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\8.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VisualStudio\8.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\8.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VCExpress\8.0\Setup\VC\ProductDir'
                ]),
                EnvFinder([
                    'VS80COMNTOOLS'
                ], '../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 8\VC',
                    r'C:\Program Files\Microsoft Visual Studio 8\VC'
                ])
            ],
            script=ScriptFinder('${MSVC.VSINSTALL}/Common7/Tools/vcvars32.bat'),
            subst_vars={
                'VCINSTALL': '${MSVC.INSTALL_ROOT}',
                'VSINSTALL': '${MSVC.INSTALL_ROOT}/..',
                'FRAMEWORK_ROOT': framework_root(),
                'FRAMEWORK_ROOT64': framework_root64()
            },
            shell_vars={
                'PATH':
                '${MSVC.VCINSTALL}/bin' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/bin' + os.pathsep +
                '${MSVC.VCINSTALL}/VCPackages' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/IDE' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/Tools' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/Tools/bin' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/bin' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'INCLUDE':
                '${MSVC.VCINSTALL}/ATLMFC/INCLUDE' + os.pathsep +
                '${MSVC.VCINSTALL}/INCLUDE' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/include' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/include',
                'LIB':
                '${MSVC.VCINSTALL}/ATLMFC/LIB' + os.pathsep +
                '${MSVC.VCINSTALL}/lib' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/lib' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/lib' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'LIBPATH':
                '${MSVC.VCINSTALL}/ATLMFC/LIB' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/lib' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/lib' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'SYSTEMROOT': SCons.Platform.win32.get_system_root()
            },
            test_file='cl.exe'
        )
    ]
)

# 64-bit native
msvc.Register(
    hosts=[SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        ToolInfo(
            version='8.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\8.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\8.0\Setup\VC\ProductDir'
                ]),
                EnvFinder([
                    'VS80COMNTOOLS'
                ], '../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 8\VC'

                ])
            ],
            script=ScriptFinder('${MSVC.VCINSTALL}/bin/amd64/vcvarsamd64.bat'),
            subst_vars={
                'VCINSTALL': '${MSVC.INSTALL_ROOT}',
                'VSINSTALL': '${MSVC.INSTALL_ROOT}/..',
                'FRAMEWORK_ROOT': framework_root(),
                'FRAMEWORK_ROOT64': framework_root64()
            },
            shell_vars={
                'PATH':
                '${MSVC.VCINSTALL}/bin/amd64' + os.pathsep +
                '${MSVC.VCINSTALL}/bin' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/bin/win64/amd64' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/bin' + os.pathsep +
                '${MSVC.VCINSTALL}/VCPackages' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/IDE' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/Tools' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/Tools/bin' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/bin' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'INCLUDE':
                '${MSVC.VCINSTALL}/ATLMFC/INCLUDE' + os.pathsep +
                '${MSVC.VCINSTALL}/INCLUDE' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK\include' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/include',
                'LIB':
                '${MSVC.VCINSTALL}/ATLMFC/LIB/AMD64' + os.pathsep +
                '${MSVC.VCINSTALL}/lib/AMD64' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/lib/AMD64' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/lib/AMD64' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'LIBPATH':
                '${MSVC.VCINSTALL}/ATLMFC/LIB/AMD64' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/lib/AMD64' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/libAMD64' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'SYSTEMROOT': SCons.Platform.win32.get_system_root()
            },
            test_file='amd64/cl.exe'
        )
    ]
)
# 64-bit cross
msvc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        ToolInfo(
            version='8.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\8.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VisualStudio\8.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\8.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VCExpress\8.0\Setup\VC\ProductDir'
                ]),
                EnvFinder([
                    'VS80COMNTOOLS'
                ], '../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 8\VC'

                ])
            ],
            script=ScriptFinder('${MSVC.VCINSTALL}/bin/x86_amd64/vcvarsx86_amd64.bat'),
            subst_vars={
                'VCINSTALL': '${MSVC.INSTALL_ROOT}',
                'VSINSTALL': '${MSVC.INSTALL_ROOT}/..',
                'FRAMEWORK_ROOT': framework_root(),
                'FRAMEWORK_ROOT64': framework_root64()
            },
            shell_vars={
                'PATH':
                '${MSVC.VCINSTALL}/bin/x86_amd64' + os.pathsep +
                '${MSVC.VCINSTALL}/bin' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/bin' + os.pathsep +
                '${MSVC.VCINSTALL}/VCPackages' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/IDE' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/Tools' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/Tools/bin' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/bin' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'INCLUDE':
                '${MSVC.VCINSTALL}/ATLMFC/INCLUDE' + os.pathsep +
                '${MSVC.VCINSTALL}/INCLUDE' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/include' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/include',
                'LIB':
                '${MSVC.VCINSTALL}/ATLMFC/LIB/AMD64' + os.pathsep +
                '${MSVC.VCINSTALL}/lib/AMD64' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/lib/AMD64' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/lib/AMD64' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'LIBPATH':
                '${MSVC.VCINSTALL}/ATLMFC/LIB/AMD64' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/lib/AMD64' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/lib/AMD64' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'SYSTEMROOT': SCons.Platform.win32.get_system_root()
            },
            test_file='x86_amd64/cl.exe'
        )
    ]
)

# ia64-bit native
msvc.Register(
    hosts=[SystemPlatform('win32', 'ia64')],
    targets=[SystemPlatform('win32', 'ia64')],
    info=[
        ToolInfo(
            version='8.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\8.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\8.0\Setup\VC\ProductDir',
                ]),
                EnvFinder([
                    'VS80COMNTOOLS'
                ], '../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 8\VC'

                ])
            ],
            script=ScriptFinder('${MSVC.VCINSTALL}/bin/ia64/vcvarsia64.bat'),
            subst_vars={
                'VCINSTALL': '${MSVC.INSTALL_ROOT}',
                'VSINSTALL': '${MSVC.INSTALL_ROOT}/..',
                'FRAMEWORK_ROOT': framework_root(),
                'FRAMEWORK_ROOT64': framework_root64()
            },
            shell_vars={
                'PATH':
                '${MSVC.VCINSTALL}/bin/ia64' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/bin/win64/ia64' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/bin' + os.pathsep +
                '${MSVC.VCINSTALL}/VCPackages' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/IDE' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/Tools' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/Tools/bin' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/bin' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'INCLUDE':
                '${MSVC.VCINSTALL}/ATLMFC/INCLUDE' + os.pathsep +
                '${MSVC.VCINSTALL}/INCLUDE' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/include' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/include',
                'LIB':
                '${MSVC.VCINSTALL}/ATLMFC/LIB/ia64' + os.pathsep +
                '${MSVC.VCINSTALL}/lib/ia64' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/lib/ia64' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/lib/ia64' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'LIBPATH':
                '${MSVC.VCINSTALL}/ATLMFC/LIB/ia64' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/lib/ia64' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/lib/ia64' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'SYSTEMROOT': SCons.Platform.win32.get_system_root()
            },
            test_file='cl.exe'
        )
    ]
)

# ia64-bit cross
msvc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'ia64')],
    info=[
        ToolInfo(
            version='8.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\8.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VisualStudio\8.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\8.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VCExpress\8.0\Setup\VC\ProductDir'
                ]),
                EnvFinder([
                    'VS80COMNTOOLS'
                ], '../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 8\VC'

                ])
            ],
            script=ScriptFinder('${MSVC.VCINSTALL}/bin/x86_ia64/vcvarsx86_ia64.bat'),
            subst_vars={
                'VCINSTALL': '${MSVC.INSTALL_ROOT}',
                'VSINSTALL': '${MSVC.INSTALL_ROOT}/..',
                'FRAMEWORK_ROOT': framework_root(),
                'FRAMEWORK_ROOT64': framework_root64()
            },
            shell_vars={
                'PATH':
                '${MSVC.VCINSTALL}/bin/x86_ia64' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/bin' + os.pathsep +
                '${MSVC.VCINSTALL}/VCPackages' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/IDE' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/Tools' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/Tools/bin' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/bin' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'INCLUDE':
                '${MSVC.VCINSTALL}/ATLMFC/INCLUDE' + os.pathsep +
                '${MSVC.VCINSTALL}/INCLUDE' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/include' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/include',
                'LIB':
                '${MSVC.VCINSTALL}/ATLMFC/LIB/ia64' + os.pathsep +
                '${MSVC.VCINSTALL}/lib/ia64' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/lib/ia64' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/lib/ia64' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'LIBPATH':
                '${MSVC.VCINSTALL}/ATLMFC/LIB/ia64' + os.pathsep +
                '${MSVC.VCINSTALL}/PlatformSDK/lib/ia64' + os.pathsep +
                '${MSVC.VSINSTALL}/SDK/v2.0/lib/ia64' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'SYSTEMROOT': SCons.Platform.win32.get_system_root()
            },
            test_file='cl.exe'
        )
    ]
)
