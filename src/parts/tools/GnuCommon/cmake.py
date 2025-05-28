from parts.platform_info import SystemPlatform
from parts.tools.Common.Finders import PathFinder

from .common import GnuInfo, cmake

cmake.Register(
    hosts=[SystemPlatform('any', 'any')],
    targets=[SystemPlatform('any', 'any')],
    info=[
        GnuInfo(
            # standard location, however there might be
            # some posix offshoot that might tweak this directory
            # so we allow this to be set
            install_scanner=[
                PathFinder(['/usr/bin'])
            ],
            opt_dirs=[
                '/usr/local/bin',
                '/usr/local/cmake/bin',
                ],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${CMAKE.INSTALL_ROOT}'},
            test_file='cmake',
        )
    ]
)

cmake.Register(
    hosts=[SystemPlatform('any', 'any')],
    targets=[SystemPlatform('any', 'any')],
    info=[
        GnuInfo(
            # standard location, however there might be
            # some posix offshoot that might tweak this directory
            # so we allow this to be set
            install_scanner=[
                PathFinder(['/usr/bin'])
            ],
            opt_dirs=[
                '/usr/local/bin',
                '/usr/local/cmake/bin',
            ],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${CMAKE.INSTALL_ROOT}'},
            test_file='cmake3',
        )
    ]
)
