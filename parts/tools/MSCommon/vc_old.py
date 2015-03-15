from common import msvc, framework_root, framework_root64
from parts.tools.Common.ToolInfo import ToolInfo
from parts.tools.Common.Finders import RegFinder,EnvFinder,PathFinder,ScriptFinder
from parts.platform_info import SystemPlatform
import os
import SCons.Platform

# version 7.1 2003

# 32-bit
msvc.Register(
    hosts=[SystemPlatform('win32','any')],
    targets=[SystemPlatform('win32','x86')],
    info=[
        ToolInfo(
            version='7.1',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\7.1\Setup\VC\ProductDir',
                    r'Software\Microsoft\Microsoft\VisualStudio\7.1\Setup\VC\ProductDir'
                ]),
                EnvFinder([
                    'VS71COMNTOOLS'
                ],'../../'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio .net 2003',
                    r'C:\Program Files\Microsoft Visual Studio .net 2003'
                ])
            ],
            script=ScriptFinder('${MSVC.VSINSTALL}/Common7/Tools/vcvars32.bat'),
            subst_vars={
            'VCINSTALL':'${MSVC.INSTALL_ROOT}',
            'VSINSTALL':'${MSVC.INSTALL_ROOT}',
            'FRAMEWORK_ROOT':framework_root(),
            'FRAMEWORK_ROOT64':framework_root64()
            },
            shell_vars={
                        'PATH':
                            '${MSVC.VCINSTALL}/bin'+os.pathsep+
                            '${MSVC.VCINSTALL}/PlatformSDK/bin'+os.pathsep+
                            '${MSVC.VCINSTALL}/VCPackages'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common7/IDE'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common7/Tools'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common7/Tools/bin'+os.pathsep+
                            '${MSVC.VSINSTALL}/SDK/v1.1/Bin'                            
                            ,
                        'INCLUDE':
                            '${MSVC.VCINSTALL}/ATLMFC/INCLUDE'+os.pathsep+
                            '${MSVC.VCINSTALL}/INCLUDE'+os.pathsep+
                            '${MSVC.VCINSTALL}/PlatformSDK/include'+os.pathsep+
                            '${MSVC.VSINSTALL}/SDK/v1.1/include'
                        ,
                        'LIB':
                            '${MSVC.VCINSTALL}/ATLMFC/LIB'+os.pathsep+
                            '${MSVC.VCINSTALL}/lib'+os.pathsep+
                            '${MSVC.VCINSTALL}/PlatformSDK/lib'+os.pathsep+
                            '${MSVC.VSINSTALL}/SDK/v1.1/lib'
                        ,
                        'LIBPATH':
                            '${MSVC.VCINSTALL}/ATLMFC/LIB'+os.pathsep+
                            '${MSVC.VCINSTALL}/PlatformSDK/lib'+os.pathsep+
                            '${MSVC.VSINSTALL}/SDK/v1.1/lib'
                        ,
                        'SYSTEMROOT':SCons.Platform.win32.get_system_root()
                        
                        
                        },
            test_file='cl.exe'
            )
        ]
    )
    
# version 7.0 2002

# 32-bit
msvc.Register(
    hosts=[SystemPlatform('win32','any')],
    targets=[SystemPlatform('win32','x86')],
    info=[
        ToolInfo(
            version='7.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\7.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\Microsoft\VisualStudio\7.0\Setup\VC\ProductDir'
                ]),
                EnvFinder([
                    'VSCOMNTOOLS'
                ],'../../'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio .NET',
                    r'C:\Program Files\Microsoft Visual Studio .NET'
                ])
            ],
            script=ScriptFinder('${MSVC.VSINSTALL}/Common7/Tools/vsvars32.bat'),
            subst_vars={
            'VCINSTALL':'${MSVC.INSTALL_ROOT}',
            'VSINSTALL':'${MSVC.INSTALL_ROOT}',
            'FRAMEWORK_ROOT':framework_root(),
            'FRAMEWORK_ROOT64':framework_root64()
            },
            shell_vars={
                        'PATH':
                            '${MSVC.VCINSTALL}/bin'+os.pathsep+
                            '${MSVC.VCINSTALL}/PlatformSDK/bin'+os.pathsep+
                            '${MSVC.VCINSTALL}/VCPackages'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common7/IDE'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common7/Tools'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common7/Tools/bin'+os.pathsep+
                            '${MSVC.VSINSTALL}/FrameworkSDK/Bin'                          
                            ,
                        'INCLUDE':
                            '${MSVC.VCINSTALL}/ATLMFC/INCLUDE'+os.pathsep+
                            '${MSVC.VCINSTALL}/INCLUDE'+os.pathsep+
                            '${MSVC.VCINSTALL}/PlatformSDK/include'+os.pathsep+
                            '${MSVC.VSINSTALL}/FrameworkSDK/include'
                            
                        ,
                        'LIB':
                            '${MSVC.VCINSTALL}/ATLMFC/LIB'+os.pathsep+
                            '${MSVC.VCINSTALL}/lib'+os.pathsep+
                            '${MSVC.VCINSTALL}/PlatformSDK/lib'+os.pathsep+
                            '${MSVC.VSINSTALL}/FrameworkSDK/lib'
                        ,
                        'SYSTEMROOT':SCons.Platform.win32.get_system_root()
                        
                        
                        },
            test_file='cl.exe'
            )
        ]
    )
    
# version 6.0 

# 32-bit
msvc.Register(
    hosts=[SystemPlatform('win32','any')],
    targets=[SystemPlatform('win32','x86')],
    info=[
        ToolInfo(
            version='6.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\6.0\Setup\Microsoft Visual C++\ProductDir',
                    r'Software\Microsoft\Microsoft\VisualStudio\6.0\Setup\Microsoft Visual C++\ProductDir'
                ]),
                EnvFinder([
                    'VS60COMNTOOLS'
                ],'../../VC98'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio/VC98',
                    r'C:\Program Files\Microsoft Visual Studio/VC98'
                ])
            ],
            script=ScriptFinder('${MSVC.VCINSTALL}/bin/vcvars32.bat'),
            subst_vars={
            'VCINSTALL':'${MSVC.INSTALL_ROOT}',
            'VSINSTALL':'${MSVC.INSTALL_ROOT}/..'
            },
            shell_vars={
                        'PATH':
                            '${MSVC.VCINSTALL}/bin/'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common/msdev98/BIN/'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common/TOOLS/'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common/TOOLS/WINNT/'                            
                            ,
                        'INCLUDE':
                            '${MSVC.VCINSTALL}/ATL/INCLUDE/'+os.pathsep+
                            '${MSVC.VCINSTALL}/MFC/INCLUDE/'+os.pathsep+
                            '${MSVC.VCINSTALL}/INCLUDE/'
                        ,
                        'LIB':
                            '${MSVC.VCINSTALL}/MFC/LIB'+os.pathsep+
                            '${MSVC.VCINSTALL}/lib/'
                        ,
                        'SYSTEMROOT':SCons.Platform.win32.get_system_root()
                                                
                        },
            test_file='cl.exe'
            )
        ]
    )    
