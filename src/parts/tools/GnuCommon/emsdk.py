import os

import parts.api as api
from parts.platform_info import SystemPlatform
from parts.tools.Common.Finders import EnvFinder

from .common import GnuInfo, emsdk

# emsdk installs the emscripten compiler frontends (emcc/em++) under
# $EMSDK/upstream/emscripten. $EMSDK is exported by emsdk's own emsdk_env.sh.
# EnvFinder resolves it lazily at scan time (not captured at import), so it
# tolerates emsdk being installed anywhere and $EMSDK being set up after parts
# is imported. The binutils live in $EMSDK/upstream/bin (see binutilsinfo.py).
EMSDK_EMSCRIPTEN_REL = 'upstream/emscripten'
EMSDK_BIN_REL = 'upstream/bin'

# Registered for visibility and so a part/parts-site can reference it; defaults
# to the value emsdk_env.sh exports. Tool *detection* uses the EnvFinder below
# (the OS EMSDK var), so this is a convenience variable, not the detection path.
api.register.add_variable(
    'EMSDK', os.environ.get('EMSDK', ''),
    'Root of the emscripten SDK (normally exported by emsdk_env.sh); emcc/em++ live under $EMSDK/upstream/emscripten')

emsdk.Register(
    hosts=[SystemPlatform('any', 'any')],
    targets=[SystemPlatform('emscripten', 'wasm32'), SystemPlatform('emscripten', 'wasm64')],
    info=[
        GnuInfo(
            install_scanner=[EnvFinder(['EMSDK'], EMSDK_EMSCRIPTEN_REL)],
            opt_dirs=[],
            script=None,
            subst_vars={},
            shell_vars={'PATH': '${EMSDK.INSTALL_ROOT}'},
            test_file='emcc',
        )
    ]
)
