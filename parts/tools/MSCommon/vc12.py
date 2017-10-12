from common import msvc, framework_root, framework_root64, get_current_sdk
from parts.tools.Common.ToolInfo import ToolInfo
from parts.tools.Common.Finders import RegFinder, EnvFinder, PathFinder, ScriptFinder
from parts.platform_info import SystemPlatform
import os
import SCons.Platform

# Need to verify the paths, but this seems to work well enough.

# version 11 .. 2012
# 32-bit
msvc.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        ToolInfo(
            version='12.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\12.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VisualStudio\12.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\12.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VCExpress\12.0\Setup\VC\ProductDir'
                ]),
                EnvFinder([
                    'VS120COMNTOOLS'
                ], '../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 12.0\VC',
                    r'C:\Program Files\Microsoft Visual Studio 12.0\VC'
                ])
            ],
            script=ScriptFinder('${MSVC.VCINSTALL}/vcvarsall.bat'),
            subst_vars={
                'VCINSTALL': '${MSVC.INSTALL_ROOT}',
                'VSINSTALL': '${MSVC.INSTALL_ROOT}/..',
                'FRAMEWORK_ROOT': framework_root(),
                'FRAMEWORK_ROOT64': framework_root64()
            },
            shell_vars={},
            test_file='cl.exe'
        )
    ]
)

msvc.Register(
    hosts=[SystemPlatform('win32', 'x86'), SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('win32', 'arm')],
    info=[
        ToolInfo(
            version='12.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\12.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VisualStudio\12.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\12.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VCExpress\12.0\Setup\VC\ProductDir'
                ]),
                EnvFinder([
                    'VS120COMNTOOLS'
                ], '../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 12.0\VC',
                    r'C:\Program Files\Microsoft Visual Studio 12.0\VC'
                ])
            ],
            script=ScriptFinder('${MSVC.VCINSTALL}/bin/x86_arm/vcvarsx86_arm.bat'),
            subst_vars={
                'VCINSTALL': '${MSVC.INSTALL_ROOT}',
                'VSINSTALL': '${MSVC.INSTALL_ROOT}/..',
                'FRAMEWORK_ROOT': framework_root(),
                'FRAMEWORK_ROOT64': framework_root64()
            },
            shell_vars={},
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
            version='12.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\12.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\12.0\Setup\VC\ProductDir',
                ]),
                EnvFinder([
                    'VS120COMNTOOLS'
                ], '../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 12.0\VC'
                ])
            ],
            script=ScriptFinder('${MSVC.VCINSTALL}/bin/AMD64/vcvars64.bat'),
            subst_vars={
                'VCINSTALL': '${MSVC.INSTALL_ROOT}',
                'VSINSTALL': '${MSVC.INSTALL_ROOT}/..',
                'FRAMEWORK_ROOT': framework_root(),
                'FRAMEWORK_ROOT64': framework_root64()
            },
            shell_vars={},
            test_file='cl.exe'
        )
    ]
)

# cross - 64-bit.
msvc.Register(
    hosts=[SystemPlatform('win32', 'any')],  # say 'any' as the code will preffer this less than a native version
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        ToolInfo(
            version='12.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\12.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VisualStudio\12.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\12.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VCExpress\12.0\Setup\VC\ProductDir'
                ]),
                EnvFinder([
                    'VS120COMNTOOLS'
                ], '../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 12.0\VC'
                    r'C:\Program Files\Microsoft Visual Studio 12.0\VC'
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
            },
            test_file='cl.exe'
        )
    ]
)

# ia64.. support gone..
