from __future__ import absolute_import, division, print_function

from parts.platform_info import SystemPlatform

from .Finders import MsiFinder, PathFinder
from .ToolInfo import ToolInfo
from .ToolSetting import ToolSetting

java = ToolSetting('java')

java.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('any', 'any')],
    info=[
        ToolInfo(
            version='1.6.0',
            install_scanner=[
                MsiFinder(r'^Java\W.*Development', r'ss160\d+$', subDir='bin'),
                PathFinder([r'c://jdk1.6.*/bin/', 'c://program files/java/jdk1.6*/bin/']),
            ],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${JAVA.INSTALL_ROOT}'},
            test_file='javac.exe'
        ),
        ToolInfo(
            version='1.7.0',
            install_scanner=[
                MsiFinder(r'^Java\W.*Development', r'ss170\d+$', subDir='bin'),
                PathFinder([r'c://jdk1.7.*/bin/', 'c://program files/java/jdk1.7*/bin/']),
            ],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${JAVA.INSTALL_ROOT}'},
            test_file='javac.exe'
        )
    ],
)

java.Register(
    hosts=[SystemPlatform('posix', 'any')],
    targets=[SystemPlatform('any', 'any')],
    info=[
        ToolInfo(
            version='1.4.0',
            install_scanner=[
                PathFinder(['/usr/bin'])
            ],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${JAVA.INSTALL_ROOT}'},
            test_file='javac'
        ),
        ToolInfo(
            version='1.6.0',
            install_scanner=[
                PathFinder(['/usr/java/jdk1.6.0*/bin', '/opt/jdk1.6.0*/bin'])
            ],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${JAVA.INSTALL_ROOT}'},
            test_file='javac'
        ),
        ToolInfo(
            version='1.7.0',
            install_scanner=[
                PathFinder(['/usr/java/jdk1.7.0*/bin', '/opt/jdk1.7.0*/bin'])
            ],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${JAVA.INSTALL_ROOT}'},
            test_file='javac'
        ),
    ],
)

java.Register(
    hosts=[SystemPlatform('darwin', 'any')],
    targets=[SystemPlatform('any', 'any')],
    info=[
        ToolInfo(
            version='1.4.0',
            install_scanner=[
                PathFinder(['/usr/bin'])
            ],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${JAVA.INSTALL_ROOT}'},
            test_file='javac'
        ),
        ToolInfo(
            version='1.6.0',
            install_scanner=[
                PathFinder(['/usr/java/jdk1.6.0*/bin', '/opt/jdk1.6.0*/bin'])
            ],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${JAVA.INSTALL_ROOT}'},
            test_file='javac'
        ),
        ToolInfo(
            version='1.7.0',
            install_scanner=[
                PathFinder(['/usr/java/jdk1.7.0*/bin', '/opt/jdk1.7.0*/bin'])
            ],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${JAVA.INSTALL_ROOT}'},
            test_file='javac'
        ),
    ],
)

# vim: set et ts=4 sw=4 ai ft=python :
