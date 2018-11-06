from __future__ import absolute_import, division, print_function


import os

from parts.platform_info import SystemPlatform
from parts.tools.Common.Finders import (EnvFinder, PathFinder, RegFinder,
                                        ScriptFinder)
from parts.tools.Common.ToolInfo import ToolInfo

from .common import vssdk


class MapLib(object):

    def __call__(self, target, source, env, for_signature):
        return env.isConfigBasedOn('debug') and 'debug' or 'retail'


vssdk.Register(
    hosts=[SystemPlatform('win32', 'any')],
    targets=[SystemPlatform('win32', 'x86')],
    info=[
        ToolInfo(
            version='8.0.60728',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\VSIP\8.0.60728\InstallDir',
                    r'Software\Microsoft\VisualStudio\VSIP\8.0.60728\InstallDir'
                ]),
                PathFinder([
                    r'C:\Program Files (x86)\Visual Studio 2005 SDK\2006.08',
                    r'C:\Program Files\Visual Studio 2005 SDK\2006.08'
                ])
            ],
            script=None,
            subst_vars={
                'MAPCONFIG': MapLib
            },
            shell_vars={
                'PATH':
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Tools/Bin',
                'INCLUDE':
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Common/Inc' + os.pathsep +
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Common/IDL' + os.pathsep +
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Common/Inc/office10',
                'LIB':
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Common/lib/${VSSDK.MAPCONFIG()}'

            },
            test_file='ctc.exe'
        ),


        ToolInfo(
            version='8.0.60912',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\VSIP\8.0.60912\InstallDir',
                    r'Software\Microsoft\VisualStudio\VSIP\8.0.60912\InstallDir'
                ]),
                PathFinder([
                    r'C:\Program Files (x86)\Visual Studio 2005 SDK\2006.09',
                    r'C:\Program Files\Visual Studio 2005 SDK\2006.09'
                ])
            ],
            script=None,
            subst_vars={
                'MAPCONFIG': MapLib
            },
            shell_vars={
                'PATH':
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Tools/Bin',
                'INCLUDE':
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Common/Inc' + os.pathsep +
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Common/IDL' + os.pathsep +
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Common/Inc/office10',
                'LIB':
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Common/lib/${VSSDK.MAPCONFIG()}'

            },
            test_file='ctc.exe'
        ),
        ToolInfo(
            version='8.0.61205.56',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\VSIP\8.0.61205.56\InstallDir',
                    r'Software\Microsoft\VisualStudio\VSIP\8.0.61205.56\InstallDir'
                ]),
                PathFinder([
                    r'C:\Program Files (x86)\Visual Studio 2005 SDK\2007.02',
                    r'C:\Program Files\Visual Studio 2005 SDK\2007.02'
                ])
            ],
            script=None,
            subst_vars={
                'MAPCONFIG': MapLib
            },
            shell_vars={
                'PATH':
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Tools/Bin',
                'INCLUDE':
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Common/Inc' + os.pathsep +
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Common/IDL' + os.pathsep +
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Common/Inc/office10',
                'LIB':
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Common/lib/${VSSDK.MAPCONFIG()}'

            },
            test_file='ctc.exe'
        ),
        ToolInfo(
            version='9.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\VSIP\9.0\InstallDir',
                    r'Software\Microsoft\VisualStudio\VSIP\9.0\InstallDir'
                ]),
                PathFinder([
                    r'C:\Program Files (x86)\Visual Studio 2008 SDK',
                    r'C:\Program Files\Visual Studio 2008 SDK'
                ])
            ],
            script=None,
            subst_vars={'MAPCONFIG': MapLib
                        },
            shell_vars={
                'PATH':
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Tools/Bin',
                'INCLUDE':
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Common/Inc' + os.pathsep +
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Common/IDL' + os.pathsep +
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Common/Inc/office10',
                'LIB':
                '${VSSDK.INSTALL_ROOT}/VisualStudioIntegration/Common/lib/${VSSDK.MAPCONFIG()}'

            },
            test_file='ctc.exe'
        )
    ]
)
