from __future__ import absolute_import, division, print_function


from SCons.Debug import logInstanceCreation

import parts.common as common
import parts.core.util as util
import parts.glb as glb
import parts.policy as policies
import parts.target_type as target_type
import parts.version as version


class part_ref(object):
    """description of class"""
    __slots__ = [        
        '__local_space',
        '__target',
        '__matches',
        '__stored_matches'
    ]

    def __init__(self, target, local_space=None):
        if __debug__:
            logInstanceCreation(self, 'parts.part_ref.part_ref')
        self.__local_space = local_space
        if util.isString(target):
            target = target_type.target_type(target)
        self.__target = target
        self.__matches = None
        self.__stored_matches = None

    @property
    def Matches(self):
        # returns all matches we have for this referance
        if not self.__matches:
            # We have not tested yet for a match.
            # query the Part Manager Object to get match information
            # and then store this result
            tmp = glb.engine._part_manager._from_target(
                self.__target,
                self.__local_space
            )
            if tmp is None:
                return []
            self.__matches = list(tmp)
        return self.__matches

    @property
    def StoredMatches(self):

        if self.__stored_matches:
            return self.__stored_matches
        else:
            self.__stored_matches = list(glb.engine._part_manager._from_target(
                self.__target,
                self.__local_space,
                use_stored_info=True
            ))
        return self.__stored_matches

    def __call__(self):
        return self.Matches

    @property
    def hasAmbiguousMatch(self):
        return len(self.Matches) > 1

    @property
    def hasMatch(self):
        return len(self.Matches) > 0

    @property
    def hasStoredMatch(self):
        return len(self.StoredMatches) > 0

    @property
    def hasStoredUniqueMatch(self):
        return len(self.StoredMatches) == 1

    @property
    def hasUniqueMatch(self):
        return len(self.Matches) == 1

    @property
    def UniqueMatch(self):
        return self.Matches[0]

    @property
    def StoredUniqueMatch(self):
        return self.StoredMatches[0]

    @property
    def Target(self):
        return self.__target

    def TargetStr(self):
        ret = ''
        properties = ''
        for k, v in self.Target.Properties.items():
            if k == 'version':
                if util.isString(v):
                    v = version.version_range(v + '.*')
                stmp = "   Version Range == {0}\n".format(v)

            elif k in ['target', 'target-platform', 'target_platform']:
                stmp = "   TARGET_PLATFORM = {0}\n".format(v)
            elif k in ['platform_match']:
                stmp = "   Platform Match = {0}\n".format(v)
            elif k in ['cfg', 'config', 'build-config', 'build_config']:
                stmp = "   config based on {0}\n".format(v)
            elif k == 'mode':
                stmp = "   mode has {0}\n".format(v)
            else:
                stmp = "   {0} = {1}\n".format(k, v)
            properties += stmp
        if properties != '':
            properties = properties[:-1]
        if self.Target.Name is not None and self.Target.Concept is not None:
            ts = 'with Alias of {0} and Section {1}'.format(self.Target.Name, self.Target.Concept)
        elif self.Target.Name is not None:
            ts = 'with Name of {0}'.format(self.Target.Name)
        elif self.Target.Alias is not None and self.Target.Concept is not None:
            ts = 'with Alias of {0} and Section {1}'.format(self.Target.Alias, self.Target.Concept)
        elif self.Target.Alias is not None:
            ts = 'with Alias of {0}'.format(self.Target.Alias)
        elif self.Target.Concept is not None:
            ts = 'with concept {0}'.format(self.Target.Concept)
        else:
            ts = 'Bad Target'

        if properties == '':
            return "Target {0}".format(ts)
        else:
            return "Target {0} and properties of:\n{1}".format(ts, properties)

    def AmbiguousMatchStr(self):
        matches = ''
        for pobj in self.Matches:
            matches += " Part Alias: {0}\n   Name: {1}\n".format(pobj.Alias, pobj.Name)
            stmp = ''
            for k, v in self.Target.Properties.items():
                if k == 'version':
                    if util.isString(v):
                        v = version.version_range(v + '.*')
                    if pobj.Version in v:
                        stmp = "   Version Range {0} in {1}\n".format(pobj.Version, v)

                elif k in ['target', 'target-platform', 'target_platform']:
                    if pobj.Env['TARGET_PLATFORM'] == v:
                        stmp = "   TARGET_PLATFORM {0} == {1}\n".format(pobj.Env['TARGET_PLATFORM'], v)
                elif k in ['platform_match']:
                    if pobj.PlatformMatch == v:
                        stmp = "   Platform Match {0} == {1}\n".format(pobj.PlatformMatch, v)
                elif k in ['cfg', 'config', 'build-config', 'build_config']:
                    if pobj.Env.isConfigBasedOn(v):
                        stmp = "   config based on {0}\n".format(v)
                elif k == 'mode':
                    mv = v.split(',')
                    for i in mv:
                        if i not in pobj.Mode:
                            break
                        else:
                            stmp = "   mode has {0}\n".format(v)
                else:
                    if pobj.Env['TARGET_PLATFORM'] == v:
                        stmp = "   {0} {1} == {2}\n".format(k, pobj.Env[k], v)
                matches += stmp
        if matches != '':
            matches = matches[:-1]
        return "Ambiguous matches found for {0}\n Possible matches are:\n {1} ".format(self.TargetStr(), matches)

    def NoMatchStr(self):
        return "No match found for:\n  {0}".format(self.TargetStr())

    def Clear(self):
        self.__matches = None
        self.__stored_matches = None

    # this should be a safe API for users
    def delaysubst(self, value, policy=policies.REQPolicy.warning):
        return '${{PARTSUBST("{target}","{val}",{policy})}}'.format(
            target=self.Target,
            val=value,
            policy=policy
        )
