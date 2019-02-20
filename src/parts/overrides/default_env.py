# this fix allows us to share setting with the default environment better
# this allows for better integration with SCons from the user point of view
from __future__ import absolute_import, division, print_function

import parts.api as api
import parts.glb as glb
import parts.settings as settings
import SCons.Script

# We are trying to get a path. No need to load any toolchains
glb.sconstruct_path = SCons.Script.DefaultEnvironment(tools=[]).Dir("#").abspath

scons_DefaultEnvironment = SCons.Script.DefaultEnvironment


def Part_DefaultEnvironment(*args, **kw):
    env = settings.DefaultSettings().DefaultEnvironment()
    if id(glb.engine.def_env) != id(env):
        glb.engine.def_env = env
    if args or kw:
        return env.Clone(*args, **kw)
    return env


# this updates some internal calls that can happen
SCons.Script.DefaultEnvironment = Part_DefaultEnvironment
# this allows use to update th "global" DefaultEnvironment in the SConstruct
# this is needed as the "pointer" to the orginal functions is already set
# my overide does not change this value in the globals
api.register.add_global_object('DefaultEnvironment', Part_DefaultEnvironment)
