import os

from parts.platform_info import SystemPlatform
from parts.tools.Common.Finders import (EnvFinder, PathFinder, RegFinder,
                                        ScriptFinder)
from parts.tools.Common.ToolInfo import ToolInfo
from parts.tools.Common.Scanners import GenericScanner
from .common import aocc

amd_2_posix = 'aocc-compiler-(\d+.\d+.\d+)'

aocc.Register(
    hosts=[SystemPlatform('posix', 'x86_64')],
    targets=[SystemPlatform('posix', 'x86_64')],
    info=[
        ToolInfo(
            version='3.*',
            install_scanner=GenericScanner(
                [os.path.expanduser('~'), os.path.expanduser('~/AMD'), '/opt/AMD', ],
                amd_2_posix,
                ['bin'],
                r'AOCC[_LVM.]+(\d+[.\d+]+)',
                'clang'
            ),
            script=ScriptFinder('${AOCC.INSTALL_ROOT}/setenv_AOCC.sh'),
            subst_vars={
            },
            shell_vars={
            },
            test_file='clang'
        )
    ]
)

# 64-bit 2.x
aocc.Register(
    hosts=[SystemPlatform('posix', 'x86_64')],
    targets=[SystemPlatform('posix', 'x86_64')],
    info=[
        ToolInfo(
            version='2.*',
            install_scanner=GenericScanner(
                [os.path.expanduser('~'), os.path.expanduser('~/AMD'), '/opt/AMD', ],
                amd_2_posix,
                ['bin'],
                r'AOCC[_LVM.]+(\d+[.\d+]+)',
                'clang'
            ),
            script=ScriptFinder('${AOCC.INSTALL_ROOT}/setenv_AOCC.sh'),
            subst_vars={
            },
            shell_vars={
            },
            test_file='clang'
        )
    ]
)
