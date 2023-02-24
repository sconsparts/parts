

import os
import pprint
import re
import subprocess

import parts.api as api
import parts.common
import SCons.Util
from parts.tools.Common.ToolInfo import ToolInfo
from parts.tools.Common.ToolSetting import ToolSetting
from parts.version import version_range


def makeStdBinutilsTool(env, name, compareNames):
    '''
    Helper function that is used to make a toolvar; it follows a pattern like (for example):
        tool = env.get('BINUTILS', {}).get('AR', env['AR'])
        env['AR'] = parts.tools.Common.toolvar(tool, ['ar'], env)
    '''
    try:
        tool = env.get('BINUTILS', {}).get(name, env[name])
    except KeyError:
        return
    env[name] = parts.tools.Common.toolvar(tool, compareNames, env)


def MatchVersionNumbers(verStr1, verStr2):

    major1, minor1, rev1, junk = (verStr1 + '.-1.-1.-1').split('.', 3)
    major1 = int(major1)
    minor1 = int(minor1)
    rev1 = int(rev1)

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


class GnuInfo(ToolInfo):

    def __init__(self, install_scanner, opt_dirs, script, subst_vars, shell_vars, test_file, opt_pattern=None):
        ToolInfo.__init__(self, "*", install_scanner, script, subst_vars, shell_vars, test_file)
        self.opt_paths = parts.common.make_list(opt_dirs)
        self.found = None
        self.opt_pattern = opt_pattern

    def get_default_ver(self, path):
        fullpath = path
        if os.path.isfile(fullpath):
            # this is to get the version number
            pipe = subprocess.Popen(fullpath + ' --version',
                                    shell=True,
                                    #stdin = 'devnull',
                                    stderr=subprocess.STDOUT,
                                    stdout=subprocess.PIPE)

            pipe.wait()
            line = pipe.stdout.readline()  # first line has version in??

            try:
                while line == '\r\n' or line == '\n':
                    line = pipe.stdout.readline()
            except Exception:
                pass
            match = re.search(r'[vV ]([0-9]+\.[0-9]+\.[0-9]*|[0-9]+\.[0-9]+)', line.decode())
            pipe.stdout.close()
            if match:
                line = match.group(1)
                return line

        return None

    def resolve_version(self, version):
        if self.found is None:
            return None
        k = list(self.found.keys())
        k.sort(reverse=True)
        for i in k:
            if MatchVersionNumbers(version, i):
                return i
        return None

    def version_set(self):
        return self.version

    def get_root(self, version):
        if self.found is None:
            root = ToolInfo.get_root(self, None)
            self.scan_query(root)
        if self.found is not None:
            try:
                k = sorted(self.found.keys())
                k.reverse()
                for i in k:
                    if MatchVersionNumbers(version, i):
                        return self.found[i][0]
            except KeyError:
                pass

        # no root was found
        # this is probally an error
        return None

    def get_shell_env(self, env, namespace, version, install_root, script, tool=None):
        # call base logic for exists
        ret = ToolInfo.get_shell_env(self, env, namespace, version, install_root, script, tool)
        if ret is not None and self.found is not None:
            # get correct tool value in namespace
            k = sorted(self.found.keys())
            k.reverse()
            for i in k:
                if MatchVersionNumbers(version, i):
                    tool = self.found[i][1]
                    version = i
                    break
            env[namespace].TOOL = tool
            env[namespace].VERSION = version
        return ret

    def query(self, env, namespace, root_path, use_script):
        # this logic is different as we have a built in scanner

        # If we have a root path passed in use it
        if root_path is not None:
            found = self.scan_query(root_path, False)
        elif SCons.Util.is_String(use_script):
            found = {'0.0.0': (None, None)}
        else:
            # use our build in lookup logic
            root = ToolInfo.get_root(self, None)
            found = self.scan_query(root)

        if found is None:
            return None

        ret = {}
        for v, p in found.items():
            # print "testing",v,p[0],p[1]
            tmp = self.exists(env, namespace, v, p[0], use_script, p[1])
            if tmp is not None:
                ret.update(self.make_ver_shell_env_set(v, tmp))

        return ret

    def scan_query(self, install_root, opt_scan=True):
        api.output.verbose_msgf(['gnu_info', "tool_info"], "query scan install_root={root}", root=install_root)
        if self.found is None:
            ret = {}
            reg = re.compile(self.test_file.replace('+', r'\+') + r'\-?([0-9]+\.[0-9]+\.[0-9]*|[0-9]+\.[0-9]+|[0-9]+)', re.I)
            if opt_scan == True:
                if self.opt_pattern is not None:
                    opt_reg = re.compile(self.opt_pattern, re.I)
                else:
                    opt_reg = reg
                # see if we can find a version in the optional directories provided
                # based on pattern of dir/tool-ver/bin/tool
                # this can be /opt or any other user provided directory
                for d in self.opt_paths:
                    # check that is exists and is directory
                    if os.path.isdir(d):
                        # look for all directories here that match pattern
                        for item in os.listdir(d):
                            result = opt_reg.match(item)
                            if result:
                                fullpath = os.path.join(d, item, 'bin')
                                if not os.path.exists(fullpath):
                                    continue
                                for fitem in os.listdir(fullpath):
                                    result = reg.match(fitem)
                                    if result or self.test_file == fitem:
                                        pathwtool = os.path.join(fullpath, fitem)
                                        tmp = self.get_default_ver(pathwtool)
                                        if tmp is not None:
                                            ret[tmp] = (fullpath, pathwtool)
                for d in self.opt_paths:
                    if os.path.isdir(d):
                        for fitem in os.listdir(d):
                            result = reg.match(fitem)
                            if result or self.test_file == fitem:
                                pathwtool = os.path.join(d, fitem)
                                tmp = self.get_default_ver(pathwtool)
                                if tmp is not None:
                                    ret[tmp] = (d, pathwtool)

            if install_root is not None:
                # see if in this area we have any possible matches of different versions
                # using a convension of tool-ver ( ie gcc-3.4 or gcc-3 )
                # overrides anything in /opt/...
                for item in os.listdir(install_root):
                    result = reg.match(item)
                    if result:
                        fullpath = os.path.join(install_root, item)
                        tmp = self.get_default_ver(fullpath)
                        if tmp is not None:
                            ret[tmp] = (install_root, fullpath)

                # see if we can find a default version in the directories provided
                # overrides any previous finds of same version

                tmp = self.get_default_ver(os.path.join(install_root, self.test_file))
                if tmp is not None:
                    ret[tmp] = (install_root, os.path.join(install_root, self.test_file))

                self.found = ret

        if self.found == {}:
            api.output.verbose_msgf(['gnu_info', "tool_info"], "Nothing was found!")
            return None
        api.output.verbose_msgf(['gnu_info', "tool_info"], f"Found:{pprint.pformat(ret)}")
        return self.found


gxx = ToolSetting('gxx')
gcc = ToolSetting('gcc')
clang = ToolSetting('clang')
binutils = ToolSetting('binutils')
