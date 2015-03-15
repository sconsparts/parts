
# this code overides scons build targets so we can do some processing before
# Scons tries to build the tree. This is basicaly giving us a call back hook
# That would be nice to have in SCons.

import SCons.Script.Main
from .. import glb

scons_build_targets = SCons.Script.Main._build_targets

def _build_targets(fs, options, targets, target_top):

        # call engine
    if glb.engine.Process(fs, options, targets, target_top) == False:
        ret= None
    else:
        # call Scons function is there is nothing wrong
        # with the engine/addin Process call
        ret= scons_build_targets(fs, options, targets, target_top)

    return ret

SCons.Script.Main._build_targets = _build_targets
