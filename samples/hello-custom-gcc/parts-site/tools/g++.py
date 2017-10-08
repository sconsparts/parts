
# this sample tools add to the gcc setup by adding some new configurations
# this however needs to load the existing gcc tools from Parts make sure
# everything loads as expected

# first load the gcc Toolsettings
from parts.platform_info import SystemPlatform
from parts.tools.Common.Finders import PathFinder
import parts.tools.GnuCommon.common
import parts.tools.GnuCommon.binutilsinfo as binutilsinfo


parts.tools.GnuCommon.common.gxx.Register(
    # we assume that the system has the correct libraies installed to do
    # a cross build or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix', 'x86_64')],
    targets=[SystemPlatform('posix', 'arm')],
    info=[
        parts.tools.GnuCommon.common.GnuInfo(
            # standard location, however there might be
            # some posix offshoot that might tweak this directory
            # so we allow this to be set
            install_scanner=[PathFinder(['/usr/bin'])],
            opt_dirs=['/opt/'],
            script=None,
            subst_vars={
                'OBJCOPY':'${GXX.INSTALL_ROOT}/arm-linux-gnueabi-objcopy',
            },
            shell_vars={'PATH': '${GXX.INSTALL_ROOT}'},
            test_file='arm-linux-gnueabi-g++')
    ]
)

# import g++ tool from parts ( we only need to add configurations to be loaded)
import importlib
gxx_module = importlib.import_module('parts.tools.g++')
globals().update(gxx_module.__dict__)

