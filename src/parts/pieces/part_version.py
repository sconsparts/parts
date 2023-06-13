from typing import Union
from parts.core.states import LoadState
import parts.api as api
from parts.pnode.part import Part
import parts.core.util.is_a as is_a
from parts.core.logic import VersionLogic
from parts.core.policy import ReportingPolicy
import parts.glb as glb
from parts.version import version as Version
from SCons.Debug import logInstanceCreation


def part_version(env, ver: Union[str, Version] = None, _warn=True):
    '''
    Defines the version of this part
    if no part is being defined it does nothing
    '''
    # if _warn: # need to think about if I can really do this internally
    #    api.output.verbose_msg(['warning'],'Use of env.PartVersion() is deprecated, Please us PartVersion() instead')

    if ver is None:
        # we want to return the version we have set
        return get_part_version(env)

    # is this a string, subst() it in case we have a special value to use
    def get_version(version):
        if is_a.isString(version):
            version = env.subst(version)
        return Version(version)
    ret = get_version(ver)
    # get the part object to test for various values
    # for setting and or behaviors.
    part_obj: Part = glb.engine._part_manager._from_env(env)

    # This is a test to make sure the "root" part set the part version before it tries call a sub-part
    if part_obj._cache.get('name_must_be_set') == True:
        api.output.error_msg("The Part version has to be set before any calls to Part()")

    # for setting of the version in the root part.
    # we warning vs error out to help with "fancy stuff".
    # abd for compatibility with older version of Parts
    if not part_obj.isRoot:
        api.output.warning_msgf("Version cannot be set in a sub-Part, ignoring new value of {0}".format(ret))
        return part_obj.Version

    if part_obj._cache.get("version_logic") == VersionLogic.Force:
        # we are to set the version to the value provided and ignore this value
        tmp = part_obj._cache.get('version')
        if not tmp:
            api.output.error_msg("VersionLogic.Force was set, but there was no version value defined to override with")
        tmp = get_version(tmp)
        if tmp != ret:
            policy = part_obj._cache.get("version_policy", env.get("VERSION_POLICY", ReportingPolicy.message))
            api.output.policy_msg(
                policy if policy else ReportingPolicy.message,
                ['version'],
                f"Overriding the version with the value of {tmp}"
            )
            ret = get_version(tmp)

    elif part_obj._cache.get("version_logic") in (VersionLogic.Verify, VersionLogic.StrictVerify):
        tmp = part_obj._cache.get('version')
        if not tmp and part_obj._cache.get("version_logic") == VersionLogic.StrictVerify:
            api.output.error_msg("VersionLogic.StrictVerify was set, but there was no version value defined to verify with")
        elif not tmp:
            api.output.verbose_msg(['version'],"VersionLogic.Verify was set, but there was no version value defined to verify with. Ignoring...")
            
        if tmp:
            tmp = get_version(tmp)
            if tmp != ret:
                # we wanted to test that these match
                # we default to error if they don't
                policy = part_obj._cache.get("version_policy", env.get("VERSION_LOGIC", ReportingPolicy.error))
                api.output.policy_msg(
                    policy if policy else ReportingPolicy.error,
                    ['version'],
                    f"Verify of PartVersion() failed! Expect version value of {tmp}, but value of {ret} was set"
                )
            else:
                api.output.print_msg(f"Verified PartVersion() value of {ret}")

    elif part_obj.Version != '0.0.0' and ret != part_obj.Version and part_obj.LoadState != LoadState.CACHE:
        api.output.warning_msgf(f"Version already set to {part_obj.Root.Version}, ignoring new value of {ret}")
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
api.register.add_method(part_version, 'PartVersion')
api.register.add_method(get_part_short_version, 'PartShortVersion')
