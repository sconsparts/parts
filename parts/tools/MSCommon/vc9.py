from common import msvc, framework_root, framework_root64, get_current_sdk
from parts.tools.Common.ToolInfo import ToolInfo
from parts.tools.Common.Finders import RegFinder, EnvFinder, PathFinder, ScriptFinder
from parts.platform_info import SystemPlatform
import os
import SCons.Platform

# version 9 .. 2008
# 32-bit
msvc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        ToolInfo(
            version='9.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\9.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VisualStudio\9.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\9.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VCExpress\9.0\Setup\VC\ProductDir'
                ]),
                EnvFinder([
                    'VS90COMNTOOLS'
                ], '../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC',
                    r'C:\Program Files\Microsoft Visual Studio 9.0\VC'
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
                get_current_sdk() + '/bin' + os.pathsep +
                '${MSVC.VCINSTALL}/VCPackages' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/IDE' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/Tools' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v3.5' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'INCLUDE':
                '${MSVC.VCINSTALL}/ATLMFC/INCLUDE' + os.pathsep +
                '${MSVC.VCINSTALL}/INCLUDE' + os.pathsep +
                get_current_sdk() + '/include',
                'LIB':
                '${MSVC.VCINSTALL}/ATLMFC/LIB' + os.pathsep +
                '${MSVC.VCINSTALL}/lib' + os.pathsep +
                get_current_sdk() + '/lib' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v3.5' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v2.0.50727',
                'LIBPATH':
                '${MSVC.VCINSTALL}/ATLMFC/LIB' + os.pathsep +
                get_current_sdk() + '/lib' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT}/v3.5' + os.pathsep +
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
            version='9.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\9.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\9.0\Setup\VC\ProductDir',
                ]),
                EnvFinder([
                    'VS90COMNTOOLS'
                ], '../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC'
                ])
            ],
            script=ScriptFinder('${MSVC.VCINSTALL}/bin/AMD64/vcvarsamd64.bat'),
            subst_vars={
                'VCINSTALL': '${MSVC.INSTALL_ROOT}',
                'VSINSTALL': '${MSVC.INSTALL_ROOT}/..',
                'FRAMEWORK_ROOT': framework_root(),
                'FRAMEWORK_ROOT64': framework_root64()
            },
            shell_vars={
                'PATH':
                '${MSVC.VCINSTALL}/bin/AMD64' + os.pathsep +
                '${MSVC.VCINSTALL}/bin' + os.pathsep +
                get_current_sdk() + '/bin/x64' + os.pathsep +
                get_current_sdk() + '/bin' + os.pathsep +
                '${MSVC.VCINSTALL}/VCPackages' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/IDE' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/Tools' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v3.5' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v2.0.50727',
                'INCLUDE':
                '${MSVC.VCINSTALL}/ATLMFC/INCLUDE' + os.pathsep +
                '${MSVC.VCINSTALL}/INCLUDE' + os.pathsep +
                get_current_sdk() + '/include',
                'LIB':
                '${MSVC.VCINSTALL}/ATLMFC/LIB/AMD64' + os.pathsep +
                '${MSVC.VCINSTALL}/lib/AMD64' + os.pathsep +
                get_current_sdk() + '/lib/x64' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v3.5' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v2.0.50727',
                'LIBPATH':
                '${MSVC.VCINSTALL}/ATLMFC/LIB/AMD64' + os.pathsep +
                get_current_sdk() + '/lib/x64' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v3.5' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v2.0.50727',
                'SYSTEMROOT': SCons.Platform.win32.get_system_root()
            },
            test_file='AMD64/cl.exe'
        )
    ]
)
# cross - 64-bit. This also works for ia64
msvc.Register(
    hosts=[SystemPlatform('win32', 'any')],  # say 'any' as the code will preffer this less than a native version
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        ToolInfo(
            version='9.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\9.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VisualStudio\9.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\9.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VCExpress\9.0\Setup\VC\ProductDir'
                ]),
                EnvFinder([
                    'VS90COMNTOOLS'
                ], '../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC'
                    r'C:\Program Files\Microsoft Visual Studio 9.0\VC'
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
                get_current_sdk() + '/bin/x64' + os.pathsep +
                get_current_sdk() + '/bin' + os.pathsep +
                '${MSVC.VCINSTALL}/VCPackages' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/IDE' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/Tools' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/Tools/bin' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v3.5' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v2.0.50727',
                'INCLUDE':
                '${MSVC.VCINSTALL}/ATLMFC/INCLUDE' + os.pathsep +
                '${MSVC.VCINSTALL}/INCLUDE' + os.pathsep +
                get_current_sdk() + '/include',
                'LIB':
                '${MSVC.VCINSTALL}/ATLMFC/LIB/AMD64' + os.pathsep +
                '${MSVC.VCINSTALL}/lib/AMD64' + os.pathsep +
                get_current_sdk() + '/lib/x64' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v3.5' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v2.0.50727',
                'LIBPATH':
                '${MSVC.VCINSTALL}/ATLMFC/LIB/AMD64' + os.pathsep +
                get_current_sdk() + '/lib/x64' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v3.5' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v2.0.50727',
                'SYSTEMROOT': SCons.Platform.win32.get_system_root()
            },
            test_file='x86_amd64/cl.exe'
        )
    ]
)
# ia64 native .. support gone.. or only installed with server 2008 sdk on ia64 boxes?
# ia64 cross
msvc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'ia64')],
    info=[
        ToolInfo(
            version='9.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\9.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VisualStudio\9.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\9.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VCExpress\9.0\Setup\VC\ProductDir'
                ]),
                EnvFinder([
                    'VS90COMNTOOLS'
                ], '../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC'
                    r'C:\Program Files\Microsoft Visual Studio 9.0\VC'
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
                '${MSVC.VCINSTALL}/bin' + os.pathsep +
                get_current_sdk() + '/bin/ia64' + os.pathsep +
                get_current_sdk() + '/bin' + os.pathsep +
                '${MSVC.VCINSTALL}/VCPackages' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/IDE' + os.pathsep +
                '${MSVC.VSINSTALL}/Common7/Tools' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v3.5' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v2.0.50727',
                'INCLUDE':
                '${MSVC.VCINSTALL}/ATLMFC/INCLUDE' + os.pathsep +
                '${MSVC.VCINSTALL}/INCLUDE' + os.pathsep +
                get_current_sdk() + '/include',
                'LIB':
                '${MSVC.VCINSTALL}/ATLMFC/LIB/ia64' + os.pathsep +
                '${MSVC.VCINSTALL}/lib/ia64' + os.pathsep +
                get_current_sdk() + '/lib/ia64' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v3.5' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v2.0.50727',
                'LIBPATH':
                '${MSVC.VCINSTALL}/ATLMFC/LIB/ia64' + os.pathsep +
                get_current_sdk() + '/lib/ia64' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v3.5' + os.pathsep +
                '${MSVC.FRAMEWORK_ROOT64}/v2.0.50727',
                'SYSTEMROOT': SCons.Platform.win32.get_system_root()
            },
            test_file='x86_ia64/cl.exe'
        )
    ]
)
