from common import mssdk
from parts.tools.Common.ToolInfo import ToolInfo
from parts.tools.Common.Finders import RegFinder, EnvFinder, PathFinder, ScriptFinder
from parts.platform_info import SystemPlatform
import os


# need to clean up some more as this has lots of false positives in detection

mssdk.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        ToolInfo(
            version='6.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\Microsoft SDKs\Windows\v6.0\InstallationFolder',
                    r'Software\Microsoft\Microsoft SDKs\Windows\v6.0\InstallationFolder'
                ]),
                PathFinder([
                    r'C:\Program Files\Microsoft SDKs\Windows\v6.0'
                ])
            ],
            script=None,
            subst_vars={},
            shell_vars={
                'PATH':
                '${MSSDK.INSTALL_ROOT}/bin',
                'INCLUDE':
                '${MSSDK.INSTALL_ROOT}/include',
                'LIB':
                '${MSSDK.INSTALL_ROOT}/lib',
                'LIBPATH':
                '${MSSDK.INSTALL_ROOT}/lib'
            },
            test_file='gacutil.exe'
        ),
        ToolInfo(
            version='6.0A',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\Microsoft SDKs\Windows\v6.0A\InstallationFolder',
                    r'Software\Microsoft\Microsoft SDKs\Windows\v6.0A\InstallationFolder'
                ]),
                PathFinder([
                    r'C:\Program Files\Microsoft SDKs\Windows\v6.0a'
                ])
            ],
            script=None,
            subst_vars={},
            shell_vars={
                'PATH':
                '${MSSDK.INSTALL_ROOT}/bin',
                'INCLUDE':
                '${MSSDK.INSTALL_ROOT}/include',
                'LIB':
                '${MSSDK.INSTALL_ROOT}/lib',
                'LIBPATH':
                '${MSSDK.INSTALL_ROOT}/lib'
            },
            test_file='gacutil.exe'
        ),
        ToolInfo(
            version='6.1',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\Microsoft SDKs\Windows\v6.1\InstallationFolder',
                    r'Software\Microsoft\Microsoft SDKs\Windows\v6.1\InstallationFolder'
                ]),
                PathFinder([
                    r'C:\Program Files\Microsoft SDKs\Windows\v6.1'
                ])
            ],
            script=ScriptFinder('${MSSDK.VSINSTALL}/bin/SetEnv.cmd'),
            subst_vars={
            },
            shell_vars={
                'PATH':
                '${MSSDK.INSTALL_ROOT}/bin',
                'INCLUDE':
                '${MSSDK.INSTALL_ROOT}/include',
                'LIB':
                '${MSSDK.INSTALL_ROOT}/lib',
                'LIBPATH':
                '${MSSDK.INSTALL_ROOT}/lib'
            },
            test_file='SetEnv.cmd'
        )

    ]
)

mssdk.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        ToolInfo(
            version='6.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\Microsoft SDKs\Windows\v6.0\InstallationFolder',
                    r'Software\Microsoft\Microsoft SDKs\Windows\v6.0\InstallationFolder'
                ]),
                PathFinder([
                    r'C:\Program Files\Microsoft SDKs\Windows\v6.0'
                ])
            ],
            script=None,
            subst_vars={},
            shell_vars={
                'PATH':
                '${MSSDK.INSTALL_ROOT}/bin',
                'INCLUDE':
                '${MSSDK.INSTALL_ROOT}/include',
                'LIB':
                '${MSSDK.INSTALL_ROOT}/lib/x64',
                'LIBPATH':
                '${MSSDK.INSTALL_ROOT}/lib/x64'
            },
            test_file='gacutil.exe'
        ),
        ToolInfo(
            version='6.0A',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\Microsoft SDKs\Windows\v6.0A\InstallationFolder',
                    r'Software\Microsoft\Microsoft SDKs\Windows\v6.0A\InstallationFolder'
                ]),
                PathFinder([
                    r'C:\Program Files\Microsoft SDKs\Windows\v6.0a'
                ])
            ],
            script=None,
            subst_vars={},
            shell_vars={
                'PATH':
                '${MSSDK.INSTALL_ROOT}/bin',
                'INCLUDE':
                '${MSSDK.INSTALL_ROOT}/include',
                'LIB':
                '${MSSDK.INSTALL_ROOT}/lib/x64',
                'LIBPATH':
                '${MSSDK.INSTALL_ROOT}/lib/x64'
            },
            test_file='gacutil.exe'
        ),
        ToolInfo(
            version='6.1',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\Microsoft SDKs\Windows\v6.1\InstallationFolder',
                    r'Software\Microsoft\Microsoft SDKs\Windows\v6.1\InstallationFolder'
                ]),
                PathFinder([
                    r'C:\Program Files\Microsoft SDKs\Windows\v6.1'
                ])
            ],
            script=ScriptFinder('${MSSDK.VSINSTALL}/bin/SetEnv.cmd'),
            subst_vars={
            },
            shell_vars={
                'PATH':
                '${MSSDK.INSTALL_ROOT}/bin',
                'INCLUDE':
                '${MSSDK.INSTALL_ROOT}/include',
                'LIB':
                '${MSSDK.INSTALL_ROOT}/lib/x64',
                'LIBPATH':
                '${MSSDK.INSTALL_ROOT}/lib/x64'
            },
            test_file='SetEnv.cmd'
        )

    ]
)

mssdk.Register(
    hosts=[SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('win32', 'x86_64')],
    info=[
        ToolInfo(
            version='6.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\Microsoft SDKs\Windows\v6.0\InstallationFolder',
                    r'Software\Microsoft\Microsoft SDKs\Windows\v6.0\InstallationFolder'
                ]),
                PathFinder([
                    r'C:\Program Files\Microsoft SDKs\Windows\v6.0'
                ])
            ],
            script=None,
            subst_vars={},
            shell_vars={
                'PATH':
                '${MSSDK.INSTALL_ROOT}/bin/x64',
                'INCLUDE':
                '${MSSDK.INSTALL_ROOT}/include',
                'LIB':
                '${MSSDK.INSTALL_ROOT}/lib/x64',
                'LIBPATH':
                '${MSSDK.INSTALL_ROOT}/lib/x64'
            },
            test_file='gacutil.exe'
        ),
        ToolInfo(
            version='6.0A',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\Microsoft SDKs\Windows\v6.0A\InstallationFolder',
                    r'Software\Microsoft\Microsoft SDKs\Windows\v6.0A\InstallationFolder'
                ]),
                PathFinder([
                    r'C:\Program Files\Microsoft SDKs\Windows\v6.0a'
                ])
            ],
            script=None,
            subst_vars={},
            shell_vars={
                'PATH':
                '${MSSDK.INSTALL_ROOT}/bin/x64',
                'INCLUDE':
                '${MSSDK.INSTALL_ROOT}/include',
                'LIB':
                '${MSSDK.INSTALL_ROOT}/lib/x64',
                'LIBPATH':
                '${MSSDK.INSTALL_ROOT}/lib/x64'
            },
            test_file='gacutil.exe'
        ),
        ToolInfo(
            version='6.1',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\Microsoft SDKs\Windows\v6.1\InstallationFolder',
                    r'Software\Microsoft\Microsoft SDKs\Windows\v6.1\InstallationFolder'
                ]),
                PathFinder([
                    r'C:\Program Files\Microsoft SDKs\Windows\v6.1'
                ])
            ],
            script=ScriptFinder('${MSSDK.VSINSTALL}/bin/SetEnv.cmd'),
            subst_vars={
            },
            shell_vars={
                'PATH':
                '${MSSDK.INSTALL_ROOT}/bin/x64',
                'INCLUDE':
                '${MSSDK.INSTALL_ROOT}/include',
                'LIB':
                '${MSSDK.INSTALL_ROOT}/lib/x64',
                'LIBPATH':
                '${MSSDK.INSTALL_ROOT}/lib/x64'
            },
            test_file='SetEnv.cmd'
        )

    ]
)

mssdk.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'ia64')],
    info=[
        ToolInfo(
            version='6.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\Microsoft SDKs\Windows\v6.0\InstallationFolder',
                    r'Software\Microsoft\Microsoft SDKs\Windows\v6.0\InstallationFolder'
                ]),
                PathFinder([
                    r'C:\Program Files\Microsoft SDKs\Windows\v6.0'
                ])
            ],
            script=None,
            subst_vars={},
            shell_vars={
                'PATH':
                '${MSSDK.INSTALL_ROOT}/bin',
                'INCLUDE':
                '${MSSDK.INSTALL_ROOT}/include',
                'LIB':
                '${MSSDK.INSTALL_ROOT}/lib/ia64',
                'LIBPATH':
                '${MSSDK.INSTALL_ROOT}/lib/ia64'
            },
            test_file='gacutil.exe'
        ),
        ToolInfo(
            version='6.1',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\Microsoft SDKs\Windows\v6.1\InstallationFolder',
                    r'Software\Microsoft\Microsoft SDKs\Windows\v6.1\InstallationFolder'
                ]),
                PathFinder([
                    r'C:\Program Files\Microsoft SDKs\Windows\v6.1'
                ])
            ],
            script=ScriptFinder('${MSSDK.VSINSTALL}/bin/SetEnv.cmd'),
            subst_vars={
            },
            shell_vars={
                'PATH':
                '${MSSDK.INSTALL_ROOT}/bin',
                'INCLUDE':
                '${MSSDK.INSTALL_ROOT}/include',
                'LIB':
                '${MSSDK.INSTALL_ROOT}/lib/xia64',
                'LIBPATH':
                '${MSSDK.INSTALL_ROOT}/lib/ia64'
            },
            test_file='SetEnv.cmd'
        )

    ]
)
