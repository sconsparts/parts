
from parts.core.states import LoadState
import parts.api as api
import parts.api.output as output
import parts.glb as glb
import parts.version as version
import SCons.Script
from SCons.Debug import logInstanceCreation
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment


def part_version(env, ver=None, _warn=True):
    '''
    Defines the version of this part
    if no part is being defined it does nothing
    '''
    # if _warn: # need to think about if I can really do this internally
    #    api.output.verbose_msg(['warning'],'Use of env.PartVersion() is deprecated, Please us PartVersion() instead')
    if ver is None:
        return get_part_version(env)
    ver = env.subst(ver)
    part_obj = glb.engine._part_manager._from_env(env)
    ret = version.version(ver)
    if part_obj._cache.get('name_must_be_set') == True:
        api.output.error_msg("The Part version has to be set before any calls to Part()")
    if part_obj.Version != '0.0.0' and ret != part_obj.Version and part_obj.LoadState != LoadState.CACHE:
        api.output.warning_msgf("Version already set to {0}, ignoring new value of {1}".format(part_obj.Root.Version, ret))
        return part_obj.Version

    if not part_obj.isRoot:
        api.output.warning_msgf("Version cannot be set in a sub-Part, ignoring new value of {0}".format(ret))
        return part_obj.Version

    part_obj.Version = ret

    return ret


def get_part_version(env):
    return glb.engine._part_manager._from_env(env).Version


def get_part_short_version(env):
    return glb.engine._part_manager._from_env(env).ShortVersion


class _PartVersion:

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, ver=None):
        return part_version(self.env, ver, _warn=False)


# add global for new format
api.register.add_global_parts_object('PartVersion', _PartVersion, True)

# adding logic to Scons Environment object
SConsEnvironment.PartVersion = part_version
SConsEnvironment.PartShortVersion = get_part_short_version
