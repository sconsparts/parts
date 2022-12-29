

import parts.api as api
import parts.glb as glb
import SCons.Script
from SCons.Debug import logInstanceCreation
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment


def part_name(env, name=None, parent_name=None):
    '''Defines the ID or name the developer uses to name this "part".
    Many different versions of a given part can be defined during a build.
    This allow the developer to ID what this component is and a way to later
    define DependOn(...) logic for his component
    '''
    if name is None:
        return get_part_name(env)

    pobj = glb.engine._part_manager._from_env(env)
    if pobj._cache.get('name_must_be_set') == True:
        api.output.error_msg("The Part name has to be set before any calls to Part()")

    if parent_name is not None:
        pobj._set_name(name, parent_name)
    else:
        pobj.ShortName = name
    return pobj.Name


def get_part_name(env):
    return glb.engine._part_manager._from_env(env).Name


def get_part_short_name(env):
    return glb.engine._part_manager._from_env(env).ShortName


class _PartName:

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, name=None, parent_name=None):
        return part_name(self.env, name, parent_name)


# add global for new format
api.register.add_global_parts_object('PartName', _PartName, True)

# adding logic to Scons Environment object
api.register.add_method(part_name, 'PartName')
api.register.add_method(get_part_short_name, 'PartShortName')
