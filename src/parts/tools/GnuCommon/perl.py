

from parts.platform_info import SystemPlatform
from parts.tools.Common.Finders import PathFinder, ScriptFinder
from parts.tools.Common.ToolSetting import ToolSetting

from .common import GnuInfo

perl = ToolSetting('PERL')
perl.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('any', 'any')],
    info=[
        GnuInfo(
            install_scanner=[
                PathFinder(['C:\\Perl\\bin'])
            ],
            opt_dirs=[
            ],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${PERL.INSTALL_ROOT}'},
            test_file='perl.exe'
        )
    ]
)

perl.Register(
    hosts=[SystemPlatform('win32', 'x86_64')],
    targets=[SystemPlatform('any', 'any')],
    info=[
        GnuInfo(
            install_scanner=[
                PathFinder(['C:\\Perl64\\bin']),
                PathFinder(['C:\\Perl\\bin'])
            ],
            opt_dirs=[
            ],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${PERL.INSTALL_ROOT}'},
            test_file='perl.exe'
        )
    ]
)

perl.Register(
    hosts=[SystemPlatform('posix', 'any'), SystemPlatform('darwin', 'any')],
    targets=[SystemPlatform('any', 'any')],
    info=[
        GnuInfo(
            install_scanner=[
                PathFinder(['/usr/bin'])
            ],
            opt_dirs=[
            ],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${PERL.INSTALL_ROOT}'},
            test_file='perl'
        )
    ]
)
