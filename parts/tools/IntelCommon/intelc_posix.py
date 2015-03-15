from common import Intelc,IntelcInfo
import common
import filescanner
from parts.tools.Common.Finders import RegFinder,EnvFinder,PathFinder,ScriptFinder
from parts.platform_info import SystemPlatform
import os


# 32-bit 13.0
Intelc.Register(
    hosts=[SystemPlatform('posix','any'),SystemPlatform('darwin','any')],
    targets=[SystemPlatform('posix','x86'),SystemPlatform('darwin','x86')],
    info=[
        IntelcInfo(
            version='13.*-*,2013.0.*-2013.*',
            install_scanner=filescanner.file_scanner12(
                '/opt/intel',
                common.intel_13_plus_posix,
                'ia32',
                ['ICPP_COMPILER{0}'.format(x) for x in xrange(15,12,-1)]),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/iclvars_ia32.bat'), # huh?
            subst_vars={

            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/ia32/',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB':'${INTELC.INSTALL_ROOT}/compiler/lib/ia32/'
                        },
            test_file='icc'
            )
        ]
    )

# 64-bit 13.0
Intelc.Register(
    hosts=[SystemPlatform('posix','x86_64'),SystemPlatform('darwin','x86_64')],
    targets=[SystemPlatform('posix','x86_64'),SystemPlatform('darwin','x86_64')],
    info=[
        IntelcInfo(
            version='13.*-*,2013.0.*-2013.*',
            install_scanner=filescanner.file_scanner12(
                '/opt/intel',
                common.intel_13_plus_posix,
                'intel64',
                ['ICPP_COMPILER{0}'.format(x) for x in xrange(15,12,-1)]),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/Intel64/intel64.sh'), # huh?
            subst_vars={

            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/intel64/',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB':'${INTELC.INSTALL_ROOT}/compiler/lib/intel64'
                        },
            test_file='icc'
            )
        ]
    )

# k1om 13.0
Intelc.Register(
    hosts=[SystemPlatform('posix','any')],
    targets=[SystemPlatform('posix','k1om')],
    info=[
        IntelcInfo(
            version='13.*-*,2013.0.*-2013.*',
            install_scanner=filescanner.file_scanner12(
                '/opt/intel',
                common.intel_13_plus_posix,
                'intel64_mic',
                ['ICPP_COMPILER{0}'.format(x) for x in xrange(15,12,-1)]),
            script=None,
            subst_vars={
            },
            shell_vars={'PATH':'${INTELC.INSTALL_ROOT}/bin/intel64_mic/',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/compiler/include/mic/',
                        'LIB':'${INTELC.INSTALL_ROOT}/compiler/lib/mic/'
                        },
            test_file='icc'
            )
        ]
    )

# 32-bit 12.1
Intelc.Register(
    hosts=[SystemPlatform('posix','any'),SystemPlatform('darwin','any')],
    targets=[SystemPlatform('posix','x86'),SystemPlatform('darwin','x86')],
    info=[
        IntelcInfo(
            version='12.1.*,2011.6.*-2011.*',
            install_scanner=filescanner.file_scanner12(
                '/opt/intel',
                common.intel_12_1_posix,
                'ia32',
                'ICPP_COMPILER12'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/iclvars_ia32.bat'),
            subst_vars={

            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/ia32/',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB':'${INTELC.INSTALL_ROOT}/compiler/lib/ia32/'
                        },
            test_file='icc'
            )
        ]
    )

# 64-bit 12.1
Intelc.Register(
    hosts=[SystemPlatform('posix','x86_64'),SystemPlatform('darwin','x86_64')],
    targets=[SystemPlatform('posix','x86_64'),SystemPlatform('darwin','x86_64')],
    info=[
        IntelcInfo(
            version='12.1.*,2011.6.*-2011.*',
            install_scanner=filescanner.file_scanner12(
                '/opt/intel',
                common.intel_12_1_posix,
                'intel64',
                'ICPP_COMPILER12'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/Intel64/intel64.sh'),
            subst_vars={

            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/intel64/',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB':'${INTELC.INSTALL_ROOT}/compiler/lib/intel64'
                        },
            test_file='icc'
            )
        ]
    )

# 32-bit 12.0
Intelc.Register(
    hosts=[SystemPlatform('posix','any'),SystemPlatform('darwin','any')],
    targets=[SystemPlatform('posix','x86'),SystemPlatform('darwin','x86')],
    info=[
        IntelcInfo(
            version='12.0.*,2011.0.*-2011.5.*',
            install_scanner=filescanner.file_scanner12(
                '/opt/intel',
                common.intel_12_posix,
                'ia32',
                'ICPP_COMPILER12'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/iclvars_ia32.bat'),
            subst_vars={

            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/ia32/',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB':'${INTELC.INSTALL_ROOT}/compiler/lib/ia32/'
                        },
            test_file='icc'
            )
        ]
    )

# 64-bit 12.0
Intelc.Register(
    hosts=[SystemPlatform('posix','x86_64'),SystemPlatform('darwin','x86_64')],
    targets=[SystemPlatform('posix','x86_64'),SystemPlatform('darwin','x86_64')],
    info=[
        IntelcInfo(
            version='12.0.*,2011.0.*-2011.5.*',
            install_scanner=filescanner.file_scanner12(
                '/opt/intel',
                common.intel_12_posix,
                'intel64',
                'ICPP_COMPILER12'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/Intel64/intel64.sh'),
            subst_vars={

            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/intel64/',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/compiler/include/',
                        'LIB':'${INTELC.INSTALL_ROOT}/compiler/lib/intel64'
                        },
            test_file='icc'
            )
        ]
    )
##
### 64-bit 12.0
##Intelc.Register(
##    hosts=[SystemPlatform('posix','x86')],
##    targets=[SystemPlatform('posix','x86_64')],
##    info=[
##        IntelcInfo(
##            version='11.*',
##            install_scanner=filescanner.file_scanner12(
##                '/opt/intel',
##                common.intel_12_posix,
##                'intel64',
##                'ICPP_COMPILER12'),
##            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/IA32_Intel64/intel64.sh'),
##            subst_vars={
##
##            },
##            shell_vars={
##                        'PATH':'${INTELC.INSTALL_ROOT}/bin/intel64/',
##                        'INCLUDE':'${INTELC.INSTALL_ROOT}/compiler/include/',
##                        'LIB':'${INTELC.INSTALL_ROOT}/compiler/lib/intel64'
##                        },
##            test_file='icc'
##            )
##        ]
##    )

# 32-bit 11.1
Intelc.Register(
    hosts=[SystemPlatform('posix','any'),SystemPlatform('darwin','any')],
    targets=[SystemPlatform('posix','x86'),SystemPlatform('darwin','x86')],
    info=[
        IntelcInfo(
            version='11.*',
            install_scanner=filescanner.file_scanner11(
                '/opt/intel/Compiler',
                common.intel_11_outer,
                common.intel_11_inner,
                'ia32',
                'ICPP_COMPILER11'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/iclvars_ia32.bat'),
            subst_vars={

            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/ia32/',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
                        'LIB':'${INTELC.INSTALL_ROOT}/lib/ia32/'
                        },
            test_file='icc'
            )
        ]
    )

# 64-bit 11.1
Intelc.Register(
    hosts=[SystemPlatform('posix','x86_64'),SystemPlatform('darwin','x86_64')],
    targets=[SystemPlatform('posix','x86_64'),SystemPlatform('darwin','x86_64')],
    info=[
        IntelcInfo(
            version='11.*',
                        install_scanner=filescanner.file_scanner11(
                '/opt/intel/Compiler',
                common.intel_11_outer,
                common.intel_11_inner,
                'EM64T',
                'ICPP_COMPILER11'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/IA32_Intel64/intel64.sh'),
            subst_vars={

            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/intel64/',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
                        'LIB':'${INTELC.INSTALL_ROOT}/lib/intel64'
                        },
            test_file='icc'
            )
        ]
    )



# 64-bit ia64 11.x todo
#Intelc.Register(
#    hosts=[SystemPlatform('posix','any')],
#    targets=[SystemPlatform('posix','ia64')],
#    info=[
#        IntelcInfo(
#            version='11.*',
#            install_scanner=filescanner.file_scanner11(
#                '/opt/intel/Compiler/11.0',
#                common.intel_11_outer,
#                common.intel_11_inner,
#                'ia32',
#                'ICPP_COMPILER11),
#            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ICLVars.bat'),
#            subst_vars={
#
#            },
#            shell_vars={
#                        'PATH':'${INTELC.INSTALL_ROOT}/bin/Itanium',
#                        'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
#                        'LIB':'${INTELC.INSTALL_ROOT}/lib/Itanium'
#                        },
#            test_file='icl.exe'
#            )
#        ]
#    )

# 32-bit 10.x
Intelc.Register(
    hosts=[SystemPlatform('posix','any'),SystemPlatform('darwin','any')],
    targets=[SystemPlatform('posix','x86'),SystemPlatform('darwin','x86')],
    info=[
        IntelcInfo(
            version='10.*',
            install_scanner=filescanner.file_scanner9_10(
                '/opt/intel/cc',
                common.intel_10_posix,
                'ia32',
                'ICPP_COMPILER10'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/iccvars.csh'),
            subst_vars={

            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
                        'LIB':'${INTELC.INSTALL_ROOT}/lib/'
                        },
            test_file='icc'
            )
        ]
    )

# 64-bit 10.x
Intelc.Register(
    hosts=[SystemPlatform('posix','x86_64'),SystemPlatform('darwin','x86_64')],
    targets=[SystemPlatform('posix','x86_64'),SystemPlatform('darwin','x86_64')],
    info=[
        IntelcInfo(
            version='10.*',
            install_scanner=filescanner.file_scanner9_10(
                '/opt/intel/cce',
                common.intel_10_posix,
                'EM64T',
                'ICPP_COMPILER10'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/iccvars.csh'),
            subst_vars={

            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
                        'LIB':'${INTELC.INSTALL_ROOT}/lib/'
                        },
            test_file='icc'
            )
        ]
    )

# 64-bit ia64 10.x
#Intelc.Register(
#    hosts=[SystemPlatform('posix','any')],
#    targets=[SystemPlatform('posix','ia64')],
#    info=[
#        IntelcInfo(
#            version='10.*',
#            install_scanner=filescanner.file_scanner9_10(
#                '/opt/intel/cc',
#                common.intel_10_posix,
#                'ia32',
#                'ICPP_COMPILER10'),
#            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ICLVars.bat'),
#            subst_vars={
#
#            },
#            shell_vars={
#                        'PATH':'${INTELC.INSTALL_ROOT}/bin/',
#                        'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
#                        'LIB':'${INTELC.INSTALL_ROOT}/lib/'
#                        },
#            test_file='icl.exe'
#            )
#        ]
#    )

# 9.x 64-bit
Intelc.Register(
     hosts=[SystemPlatform('posix','x86_64'),SystemPlatform('darwin','x86_64')],
     targets=[SystemPlatform('posix','x86_64'),SystemPlatform('darwin','x86_64')],
     info=[
         IntelcInfo(
             version='9.*',
             install_scanner=filescanner.file_scanner9_10(
                 '/opt/intel/cce',
                 common.intel_9_posix,
                 'EM64T',
                 'ICPP_COMPILER9'),
             script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/iccvars.csh'),
             subst_vars={

             },
             shell_vars={
                         'PATH':'${INTELC.INSTALL_ROOT}/bin/',
                         'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
                         'LIB':'${INTELC.INSTALL_ROOT}/lib/'
                         },
             test_file='icc'
             )
         ]
     )

#9.x 32-bit
Intelc.Register(
     hosts=[SystemPlatform('posix','any'),SystemPlatform('darwin','any')],
     targets=[SystemPlatform('posix','x86'),SystemPlatform('darwin','x86')],
     info=[
         IntelcInfo(
             version='9.*',
             install_scanner=filescanner.file_scanner9_10(
                 '/opt/intel/cc',
                 common.intel_9_posix,
                 'ia32',
                 'ICPP_COMPILER9'),
             script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/iccvars.csh'),
             subst_vars={

             },
             shell_vars={
                         'PATH':'${INTELC.INSTALL_ROOT}/bin/',
                         'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
                         'LIB':'${INTELC.INSTALL_ROOT}/lib/'
                         },
             test_file='icc'
             )
         ]
     )


