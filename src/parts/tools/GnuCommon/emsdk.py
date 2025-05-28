import os

from parts.platform_info import SystemPlatform
from parts.tools.Common.Finders import EnvFinder, PathFinder, ScriptFinder
from parts.tools.Common.ToolInfo import ToolInfo

from .common import GnuInfo, emsdk

emsdk_install_base = f"{os.environ.get('EMSDK')}/upstream/emscripten" if os.environ.get('EMSDK') else ""

emsdk.Register(
    hosts=[SystemPlatform('any', 'any')],
    targets=[SystemPlatform('emscripten', 'wasm32'), SystemPlatform('emscripten', 'wasm64')],
    info=[
        GnuInfo(
            # standard location, however there might be
            # some posix offshoot that might tweak this directory
            # so we allow this to be set
            install_scanner=[
                PathFinder(['/usr/bin'])
            ],
            opt_dirs=[
                emsdk_install_base
            ],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${EMSDK.INSTALL_ROOT}'},
            test_file='emcc',
        )
    ]
)
