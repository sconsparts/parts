import os

from parts.platform_info import SystemPlatform
from parts.tools.Common.Finders import EnvFinder, PathFinder, ScriptFinder
from parts.tools.Common.ToolInfo import ToolInfo

from . import android
from .common import GnuInfo, RedHatToolsetPaths, clang

# mac
clang.Register(
    # we assume that the system has the correct libraries installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('darwin', 'x86'), SystemPlatform('darwin', 'x86_64'), SystemPlatform('darwin', 'arm64')],
    targets=[SystemPlatform('darwin', 'x86'), SystemPlatform('darwin', 'x86_64'), SystemPlatform('darwin', 'arm64')],
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
            shell_vars={'PATH': '${CLANG.INSTALL_ROOT}'},
            test_file='clang',
            opt_pattern=r'clang\-?([0-9]+\.[0-9]+\.[0-9]*|[0-9]+\.[0-9]+|[0-9]+)'
        )

    ]
)

clang.Register(
    # we assume that the system has the correct libraries installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'any')],
    targets=[SystemPlatform('posix', 'any')],
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
            ] + RedHatToolsetPaths(r"llvm\-toolset\-(?:[0-9]+\.[0-9]+|[0-9]+)"), # for EL7-style llvm-toolset
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${CLANG.INSTALL_ROOT}'},
            test_file='clang',
            opt_pattern=r'clang\-?([0-9]+\.[0-9]+\.[0-9]*|[0-9]+\.[0-9]+|[0-9]+)'
        )
    ]
)
