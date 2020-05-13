

import copy

from past.builtins import cmp

import parts.api as api
import parts.api.output as output
import parts.common as common
import parts.platform_info as platform_info
import parts.version
import SCons.Errors
import SCons.Util
from parts.version import version_range
from SCons.Debug import logInstanceCreation


def MatchVersionNumbers(verStr1, verStr2):
    if isinstance(verStr1, version_range):
        return verStr2 in verStr1
    if isinstance(verStr2, version_range):
        return verStr1 in verStr2
    if verStr1[-1] == '.':
        verStr1 = verStr1[:-1]
    major1, minor1, rev1, junk = (verStr1 + '.-1.-1.-1').split('.', 3)
    major1 = int(major1)
    minor1 = int(minor1)
    rev1 = int(rev1)

    if verStr2[-1] == '.':
        verStr2 = verStr2[:-1]
    major2, minor2, rev2, junk = (verStr2 + '.-1.-1.-1').split('.', 3)
    major2 = int(major2)
    minor2 = int(minor2)
    rev2 = int(rev2)

    if major1 != major2:
        return False
    if major1 == major2 and (minor1 == -1 or minor2 == -1):
        return True
    if minor1 != minor2:
        return False
    if minor1 == minor2 and (rev1 == -1 or rev2 == -1):
        return True
    if rev1 == rev2:
        return True

    return False


def _cmp_(verStr1, verStr2):
    # till I get the upgraded version object
    major1, minor1, rev1, junk = (verStr1 + '.-1.-1.-1').split('.', 3)
    major2, minor2, rev2, junk = (verStr2 + '.-1.-1.-1').split('.', 3)
    try:
        major1 = int(major1)
        minor1 = int(minor1)
        rev1 = int(rev1)
        major2 = int(major2)
        minor2 = int(minor2)
        rev2 = int(rev2)
    except ValueError:
        return cmp(verStr1, verStr2)

    if major1 != major2:
        return cmp(major1, major2)
    if minor1 != minor2:
        return cmp(minor1, minor2)
    return cmp(rev1, rev2)


''' this class helps reports errors happen when we have some issue with setting
up the tool for the user.
'''


class ToolSetupError(SCons.Errors.UserError):
    pass


'''
This class handles mangament of tool info objects based on HOST and TARGET
platform support.

The main logic caches data based on exist or query calls. If the request for
a version is None, it will do a query ( check for all possible cases)
If the version is exact, it will test for the exact version, However the tool
info might still do a limited query. ( this happens in cases of tools that
support many drops that are side by side installable. ie request for version 9
means then find best match, which spawns match for all version matches)

To help with speed a cache is made of found versions.
a seperate items value is saved to say if the cache is a full query or not.
This allow the ability to retest

'''


class ToolSetting:

    def __init__(self, name):
        if __debug__:
            logInstanceCreation(self)

        # used as the namespace for common values such as version and script
        self.name = name.upper()
        api.output.verbose_msgf("toolsettings", "Creating Setting object {0}", self.name)
        # <name>_VERSION
        self.version_tag = self.name + '_VERSION'
        # <name>_SCRIPT
        self.script_tag = self.name + '_SCRIPT'
        # <name>_ROOTPATH
        self.rootpath_tag = self.name + '_INSTALL_ROOT'

        # supported tools
        self.tools = {}

        # tools that we found
        self.found = {}
        # tools that we have not found basic same layout given
        # if key value is None this means a full query has been done for
        # this case, else it is list of versions not found
        self.not_found = {}

        # all the requested shell env
        # cached in case we are asked again
        self.shell_cache = {}

    def best_ver_map(self, key, version):
        from parts.version import version_range as Version
        if version is None:
            return None
        k = self.found.get(key, [])
        k.sort(reverse=True)
        for i in k:
            if MatchVersionNumbers(version, i):
                return i
        return None

    def get_cache_key(self, env):
        '''
        make a cache/hash key for use to safely store a retrieve data about
        what we know or don't know at this time.
        '''
        version = env.get(self.version_tag, 'None')
        root_path = env.get(self.rootpath_tag, 'None')
        use_script = str(env.get(self.script_tag, 'False'))
        target = env['TARGET_PLATFORM']
        # return str(version)+root_path+use_script+str(target)
        return str(root_path) + str(use_script) + str(target) + env.subst("$CONFIG")

    def get_latest_known_version(self, cache_key):
        try:
            # assumes presorted when added
            return self.found[cache_key][0]
        except KeyError:
            pass
        except IndexError:
            pass
        return None

    def is_version_known(self, version, cache_key):
        '''
        see if the tool is known in our 'found' cache
        assumes that we had called query_for_known already
        '''
        try:
            return (version in self.found[cache_key])
        except KeyError:
            return False

    def query_for_known(self, env, key):
        '''
        This will query for known defaults based on enviroment value that
        could have been set by the user such as the <tool>_INSTALL_ROOT or
        <tool>_USE_SCRIPT. It will cache this data to help speed up the build.
        This should not be an issue as the scripts and environment should not
        change during the build. scripts should have a unique path
        '''

        # see if we have tested for it
        try:
            if self.not_found[key] is None:
                # this combo was fully queried
                return
        except Exception:
            pass
        api.output.verbose_msgf(['toolsettings'], "query for known")
        # don't have it, so we setup to get it added to cache
        self.found[key] = []
        self.not_found[key] = None  # set this to fully queried
        # setup target to test for
        target = env['TARGET_PLATFORM']

        t1 = copy.copy(target)
        t1.ARCH = 'any'
        t2 = copy.copy(target)
        t2.OS = 'any'
        t3 = copy.copy(t2)
        t3.ARCH = 'any'

        # test values

        version = env.get(self.version_tag, None)
        root_path = env.get(self.rootpath_tag, None)
        use_script = env.get(self.script_tag, False)
        api.output.verbose_msgf(
            ['toolsettings'],
            "query logic:\n version={version}\n root_path={root}\n use_script={script}",
            root=root_path,
            script=use_script,
            version=version
        )

        # make sure we have a target key
        if target not in self.found:
            self.found[key] = []

        # test raw target

        def query_logic(_target):
            api.output.verbose_msgf(['toolsettings'], "Query based on:{0}", _target)
            for k, vl in self.tools[_target].items():
                swap = False
                for v in vl:
                    tmp = v.query(env, self.name, root_path, use_script)

                    # if we find anything
                    if tmp is not None:
                        # go through all items and store needed information
                        for ver, senv in tmp.items():
                            common.append_unique(self.found[key], ver)
                        # move found item with front
                        if swap:
                            vl.remove(v)
                            vl.insert(0, v)
                        # if we got here we had a match... we take this and
                        # skip the rest
                        break
                    swap = True
            if self.name in env:
                del env[self.name]

        if target in self.tools:
            query_logic(target)
        # test for <OS>-any
        if t1 in self.tools:
            query_logic(t1)
        # test for any-<Arch>
        if t2 in self.tools:
            query_logic(t2)
        # test for any-any
        if t3 in self.tools:
            query_logic(t3)

        #self.found[key].sort(reverse=True, cmp=_cmp_)
        self.found[key].sort(reverse=True, key=lambda x: parts.version.version(x))

    def query_for_exact(self, env, key, version):
        '''
        This will query for known defaults based on enviroment value that
        could have been set by the user such as the <tool>_INSTALL_ROOT or
        <tool>_USE_SCRIPT. It will cache this data to help speed up the build.
        This should not be an issue as the scripts and environment should not
        change during the build. scripts should have a unique path
        '''
        # see if we have tested for it
        try:
            if self.not_found[key] is None:
                api.output.verbose_msgf(['toolsettings'], "not_found : {}", key)
                # this combo was fully queried
                return
        except Exception:
            pass
        api.output.verbose_msgf(['toolsettings'], "query for Exact version '{0}'", version)
        # don't have it, so we setup to get it added to cache
        if key not in self.found:
            self.found[key] = []
            self.not_found[key] = []

        # setup target to test for
        target = env['TARGET_PLATFORM']

        t1 = copy.copy(target)
        t1.ARCH = 'any'
        t2 = copy.copy(target)
        t2.OS = 'any'
        t3 = copy.copy(t2)
        t3.ARCH = 'any'

        # test values
        cache_key = str(version) + key
        root_path = env.get(self.rootpath_tag, None)
        use_script = env.get(self.script_tag, False)
        api.output.verbose_msgf(
            ['toolsettings'],
            "query logic root_path={root} use_script={use_script}",
            root=root_path,
            use_script=use_script
        )

        def exist_logic(_target):
            for k, vl in self.tools[_target].items():
                swap = False
                for v in vl:
                    if version in v.version_set():
                        tmp = v.exists(env, self.name, version, root_path, use_script)
                        if tmp is not None:
                            # remove the matching tool, and add to the front
                            # as it is the matching tool found
                            if swap:
                                vl.remove(v)
                                vl.insert(0, v)
                            # store that it is found.. store exact version found
                            common.append_unique(self.found[key], v.resolve_version(version))
                            # get cache key
                            # cache_key2=version+self.get_cache_key(env)
                            # store shell env vals
                            # self.shell_cache[cache_key2]=self.shell_cache[cache_key]=(tmp,env[self.name]._rebind(None,None))
                            # make sure it is sorted corrcetly
                            self.found[key].sort(reverse=True)
                            return True
                    swap = True
            return False

        # test raw target
        if target in self.tools:
            if exist_logic(target):
                return

        # test for <OS>-any
        if t1 in self.tools:
            if exist_logic(t1):
                return
        # test for any-<Arch>
        if t2 in self.tools:
            if exist_logic(t2):
                return
        # test for any-any
        if t3 in self.tools:
            if exist_logic(t3):
                return

        self.not_found[key].append(version)

    def Exists(self, env, tool=None, **kw):
        '''
        primary user function to see if what we want exists
        '''

        # clone env so we test with out messing up current state
        tenv = env.Clone(**kw)
        # get cache key for this enviroment setup
        key = self.get_cache_key(tenv)
        # Get version value
        version = env.get(self.version_tag, None)
        if version is None:
            # if none we query for all
            # do query for all known that match this setup
            self.query_for_known(tenv, key)
            # set version to latest found
            version = self.get_latest_known_version(key)
        else:
            # query for exact match
            self.query_for_exact(tenv, key, version)

        # test to see if it was found
        found = self.is_version_known(version, key)
        if tool is not None and found == True:
            try:
                tpath = self.get_shell_env(env)[0]['PATH']
                tmp = SCons.Util.WhereIs(tool, path=tpath)

                if tmp is not None:
                    found = True
            except Exception:
                found = False

        # test to see if it was found
        return found

    def GetInfo(self, env, version, target, root_path, use_script):
        '''
        Get the information. It is expected that the caller has done the
        correct tests to validate that the can get information out of this
        info object correctly, or that it exists.
        '''
        import copy
        t1 = copy.copy(target)
        t1.ARCH = 'any'
        t2 = copy.copy(target)
        t2.OS = 'any'
        t3 = copy.copy(t2)
        t3.ARCH = 'any'
        # we try to get the supported information
        # based on best match.
        # Platform is given priority to architecture
        ret = None

        if target in self.tools:
            for k, vl in self.tools[target].items():
                for v in vl:
                    if version in v.version_set() and v.exists(env, self.name, version, root_path, use_script):
                        return v
        if t1 in self.tools:
            for k, vl in self.tools[t1].items():
                for v in vl:
                    if version in v.version_set() and v.exists(env, self.name, version, root_path, use_script):
                        return v
        if t2 in self.tools:
            for k, vl in self.tools[t2].items():
                for v in vl:
                    if version in v.version_set() and v.exists(env, self.name, version, root_path, use_script):
                        return v
        if t3 in self.tools:
            for k, vl in self.tools[t3].items():
                for v in vl:
                    if version in v.version_set() and v.exists(env, self.name, version, root_path, use_script):
                        return v

        return ret

    def merge_tools(self, target, tools, host):

        try:
            # get the existing item in target
            items = self.tools[target]
        except KeyError:
            # not defined so we just add the set and return
            api.output.verbose_msgf(
                "toolsettings", "For tool: '{0}' host: '{3}' adding info for target:{1} verions:{2}", self.name, target, [
                    str(i) for i in list(
                        tools.keys())], host)
            self.tools[target] = tools
            return

        api.output.verbose_msgf(
            "toolsettings", "For tool: '{0}' host: '{3}' adding info for target:{1} verions:{2}", self.name, target, [
                str(i) for i in list(
                    tools.keys())], host)
        for key, val in tools.items():
            # if we have this version already
            if key in items:
                # only add it if the key is native
                if val[0].is_native:
                    items[key] = val + items[key]
                else:
                    items[key].extend(val)
            else:
                items[key] = val

    def Register(self, hosts, targets, info):
        '''
        Called by user to register a given set of Tool Information objects
        that support some build host and target combination
        '''

        hosts = common.make_list(hosts)
        targets = common.make_list(targets)
        info = common.make_list(info)

        # iterate all the hosts ignore items that are no supported on current host
        for h in hosts:
            # only need to update Hosts that match this system, ignore the rest
            if h == platform_info.HostSystem():
                tmp = {}
                # orginize the versions for easy access later
                for i in info:
                    i.is_native = h._is_native()
                    tmp[i.version] = [i]
                # add info sorted in to correct target buckets
                for t in targets:
                    self.merge_tools(t, tmp, h)

    def get_shell_env(self, env):
        '''
        This function returns the shell enviroment to be merged into the
        final SCons environment

        The trick with this function is that it really just gets data that was
        stored with the exists call. The data cached here tell us if there is
        a match or not. The Key holds data on everything but the version
        the cache_key adds the version
        '''
        # get cache key for this enviroment setup
        key = self.get_cache_key(env)
        _v = version = env.get(self.version_tag, None)
        cache_key = str(version) + key
        try:
            return self.shell_cache[cache_key]
        except KeyError:

            _env = env.Clone()

            # basic info we will need
            tinfo = None
            root_path = _env.get(self.rootpath_tag, None)
            use_script = _env.get(self.script_tag, False)
            target = _env['TARGET_PLATFORM']
            config = env.subst("$CONFIG")

            api.output.verbose_msgf(
                ['toolsettings'],
                "Getting environment for tool: {0}\n version: {1}\n use_script: {2}\n target: {3}\n config: {4}",
                self.name,
                "latest" if version is None else version,
                use_script,
                target,
                config)
            # query data
            if version is not None:
                self.query_for_exact(_env, key, version)
            else:
                self.query_for_known(_env, key)

            # get the tool info for the host-target combo for the requested version
            # get latest found version if not provided
            if version is None:
                best_version = self.get_latest_known_version(key)
            else:
                # map version to best known value found
                best_version = self.best_ver_map(key, version)
            # see if we know if the give version exists
            if self.is_version_known(best_version, key):
                tinfo = self.GetInfo(_env, best_version, target, root_path, use_script)
            else:
                # this is an error, nothing found
                # report that version is not found and the versions if any that
                # have been found

                if self.not_found[key] is not None:
                    # make sure all version are queried so we can report correctly
                    self.query_for_known(env, key)
                if self.found[key] == []:
                    raise ToolSetupError("No version of %s was found on the system for target %s" % (self.name, target))
                raise ToolSetupError("Version of %s of %s not found for target %s. Found version are %s" %
                                     (version, self.name, target, self.found[key]))

            if tinfo is None:
                raise ToolSetupError(
                    'ToolSettings failed to load infomation about tool {0} with version: {1} and target: {2}'.format(
                        self.name, version, target))
            # got the tool info now get the data

            # get the shell environment
            shell_env = tinfo.get_shell_env(_env, self.name, best_version, root_path, use_script)

            # store it in cache
            ret = (shell_env, _env[self.name]._rebind(None, None))
            self.shell_cache[cache_key] = ret
            # test to see if orginal version and install_root are None is so make a special key for them
            # this is case a tool chain uses the same setup, but they did not overide the install_Root and version
            # in this case this run woudl store a key of version=None ans root=None but after this was applied
            # this next run would have an install root, and a version of None ( given this was what they set in the toolchain
            # teh tool setup would have reset teh version, but not the install root
            if _v is None and _env.get(self.rootpath_tag, None) is None:
                root_path = ret[1]['INSTALL_ROOT']
                key = str(root_path) + str(use_script) + str(target) + config
                self.shell_cache[str(_v) + key] = ret
        return ret

    def MergeShellEnv(self, env):
        import pprint
#        pp = pprint.PrettyPrinter(indent=4)
#        pp.pprint(self.__dict__)

        version = env.get(self.version_tag, None)
        root_path = env.get(self.rootpath_tag, None)
        use_script = env.get(self.script_tag, False)
        tmp = self.get_shell_env(env)

        if tmp is None:
            raise ValueError("No shell environment defined for %s, VERSION=%s,\
                    INSTALL_ROOT=%s, Script= %s" % (self.name, version, root_path, use_script))
        # print tmp
        shell_env, ns = tmp
        # Add data to env
        for k, v in shell_env.items():
            env.PrependENVPath(k, v, delete_existing=1)
        api.output.verbose_msg('toolsettings', "env['ENV'] equal to\n", pprint.pformat(env['ENV']))
        # setup any common state
        # setup version info
        env[self.name] = ns._rebind(env, self.name)
        version = env[self.name]['VERSION']
        env[self.version_tag] = version
        env[self.rootpath_tag] = env[self.name]['INSTALL_ROOT']

        api.output.verbose_msg('toolsettings', "Tool", self.name, "configured to version:", version)
 #       import pprint
 #       pp = pprint.PrettyPrinter(indent=4)
 #       pp.pprint(self.__dict__)
