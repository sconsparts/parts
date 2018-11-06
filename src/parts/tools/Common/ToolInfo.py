
from __future__ import absolute_import, division, print_function


from builtins import range

import os

import parts.api as api
import parts.common
from parts.version import version_range

from . import Finders
import SCons.Util
from SCons.Debug import logInstanceCreation


class ToolInfo(object):

    def __init__(self, version, install_scanner, script, subst_vars, shell_vars, test_file):
        if __debug__:
            logInstanceCreation(self)
        # version of the tools this object refers to
        if '*' in version:
            self.version = version_range(version)
        else:
            self.version = version

        # list of objects or a scanner object that test for finding the root path
        self.install_root = install_scanner

        # list of objects that test and handle script processing
        self.script = script

        # the dictionary of value we need to add for correct subsitution of
        # final value for the enviroment.. ignored in cases of script handling
        self.subst_vars = subst_vars

        # The dictionary of values we want to add to the running environment
        # keys() used for script handling
        self.shell_vars = shell_vars

        # The file we use to test for a correctly setup envionrment
        self.test_file = test_file

        self.shell_cache = {}

        # state value for when we add data to the tool setting object
        # this allow use to make sure we overide certain toolinfo objects
        # when the host they are bound to is native over item that are not
        self.is_native = False

    def version_set(self):

        ret = []
        try:
            tmp = self.version.split('.')
        except AttributeError:
            return self.version
        for i in range(0, len(tmp)):
            # add path data
            ret.append(".".join(tmp[:i + 1]))
        return ret

    def resolve_version(self, version):
        try:
            return self.install_root.resolve_version(version)
        except AttributeError:
            return self.version

    def make_ver_shell_env_set(self, ver, env):
        ret = {}
        tmp = ver.split('.')
        for i in range(0, len(tmp)):
            # add path data
            ret[".".join(tmp[:i + 1])] = env
        return ret

    def get_script(self, env):
        for i in self.script:
            ret = i(env)
            if ret is not None:
                return (ret, i.args)
        return None

    def get_root(self, version):
        if SCons.Util.is_List(self.install_root):
            for i in self.install_root:
                ret = i()
                if ret is not None:
                    return os.path.normpath(ret)
        else:
            return self.install_root.resolve(version)
        # no root was found
        # this is probally an error
        return None

    def get_shell_env(self, env, namespace, version, install_root, script, tool=None):
        ret = {}
        if tool is None:
            tool = self.test_file
        if install_root is None:
            # get the install_root
            install_root = self.get_root(version)
        # Setup namespaced varibles
        env[namespace] = self.get_namespace(INSTALL_ROOT=install_root,
                                            VERSION=self.resolve_version(version),
                                            TOOL=tool)
        cache_key = str(version) + str(install_root) + str(script) + env.subst("$CONFIG")
        try:
            return self.shell_cache[cache_key]
        except KeyError:
            if SCons.Util.is_String(script) and script not in ['True', 'False', 'true', 'false', '1', '0']:
                # process the script directly
                api.output.verbose_msg("toolinfo", "Getting environment via custom script")
                if os.path.exists(script):
                    ret = env.GetScriptVariables(scripts)
                else:
                    # error as no file exits
                    pass
            elif script == True or \
                    script in ['True', 'true', '1'] or\
                    self.shell_vars == {} or\
                    self.shell_vars is None:
                api.output.verbose_msg("toolinfo", "Getting environment via tool script")
                # get the default script if one exists and use it
                if self.script is not None:
                    script_data = self.script(env)
                    if script_data is None:
                        # we have an error as script was not found
                        # we can ignore it
                        # try to warn if we have an install root
                        if install_root is not None:
                            api.output.verbose_msgf(
                                "toolinfo", "Script '{0}' not found, needed to setup tool '{1}', version '{2}'", self.script.name, tool, version, show_stack=False)
                        ret = {}
                    else:
                        ret = env.GetScriptVariables(script_data, self.script.args)
                else:
                    ret = {}

            else:  # script is False
                # subst data
                api.output.verbose_msg("toolinfo", "Getting environment via variable substution")
                for k, v in self.shell_vars.items():
                    ret[k] = os.path.normpath(env.subst(v))

        self.shell_cache[cache_key] = ret
        return ret

    def get_namespace(self, **kw):
        kw.update(self.subst_vars)
        return parts.common.namespace(**kw)

    def query(self, env, namespace, root_path, use_script):
        if SCons.Util.is_List(self.install_root):
            api.output.verbose_msg("toolinfo", "Query based on finders")
            found = {self.version: root_path}
        elif SCons.Util.is_String(use_script):  # this is incorrect...
            api.output.verbose_msg("toolinfo", "Query based on script")
            found = {'0.0.0': None}
        else:
            api.output.verbose_msg("toolinfo", "Query based on scanner object")
            found = self.install_root.scan()
        api.output.verbose_msgf("toolinfo", "Found {0}", found)
        if found is None:
            return None

        ret = {}
        for v, p in found.items():
            tmp = self.exists(env, namespace, v, p, use_script)
            api.output.verbose_msgf("toolinfo", "Exists test returned {0}", tmp)
            if tmp:
                ret[v] = tmp
                # ret.update(self.make_ver_shell_env_set(v,tmp))
        return ret

    # general case
    def exists(self, env, namespace, version, root_path, use_script, tool=None):
        shell_env = self.get_shell_env(env, namespace, version, root_path, use_script, tool)
        try:
            tpath = shell_env['PATH']
            # print "tpath=",tpath
            # print env.subst("${"+namespace+".TOOL}")
            tmp = SCons.Util.WhereIs(env.subst("${" + namespace + ".TOOL}"), path=tpath)
            # print tmp
        except KeyError:
            # this is probally wrong test to have happen
            tmp = SCons.Util.WhereIs(self.test_file)
        if tmp is not None:
            # print "FOUND"
            return shell_env
        # print "NOT FOUND"
        return None
