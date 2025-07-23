import os
import pprint
import re
import subprocess
from typing import Final, Optional, List

import parts.api as api
import parts.common
import SCons.Util
from parts.tools.Common.ToolInfo import ToolInfo
from parts.tools.Common.ToolSetting import ToolSetting

def makeStdBinutilsTool(env, name, compareNames):
    '''
    Helper function that is used to make a toolvar; it follows a pattern like (for example):
        tool = env.get('BINUTILS', {}).get('AR', env['AR'])
        env['AR'] = parts.tools.Common.toolvar(tool, ['ar'], env)
    '''
    import parts.tools.Common
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

# Get RH-style devtoolset paths for use elsewhere. Defaults to returning both EL6-7 devtoolset-<version>
# and EL8+ gcc-toolset-<version> options.
def RedHatToolsetPaths(regex: str = r"(gcc\-|dev)toolset\-\d+") -> List[str]:
    RH_OPT_PATH: Final[str] = "/opt/rh"
    RH_OPT_ROOT_SUB_PATH: Final[str] = "root/usr/bin"

    pattern = re.compile(regex)

    if os.path.exists("/opt/rh"):
        return [ os.path.join(RH_OPT_PATH, d, RH_OPT_ROOT_SUB_PATH) for d in os.listdir(RH_OPT_PATH) if pattern.fullmatch(d)]
    else:
        return []

class GnuInfo(ToolInfo):
    DEFAULT_TEST_FILE_SUFFIX_PATTERN: Final[str] = r'\-?([0-9]+\.[0-9]+\.[0-9]*|[0-9]+\.[0-9]+|[0-9]+)'
    DEFAULT_VERSION_PATTERN: Final[str] = r'[vV ]([0-9]+\.[0-9]+\.[0-9]*|[0-9]+\.[0-9]+)'

    def __init__(self, install_scanner, opt_dirs, script, subst_vars, shell_vars, test_file,
                 opt_pattern: Optional[str]=None,
                 test_file_prefix_pattern: Optional[str]=None, test_file_suffix_pattern: Optional[str]=DEFAULT_TEST_FILE_SUFFIX_PATTERN,
                 version_pattern: str=DEFAULT_VERSION_PATTERN):
        ToolInfo.__init__(self, "*", install_scanner, script, subst_vars, shell_vars, test_file)
        self.opt_paths = parts.common.make_list(opt_dirs)
        self.found: Optional[dict] = None
        self.opt_pattern: Optional[str] = opt_pattern
        self.test_file_prefix_pattern: str = test_file_prefix_pattern or ""
        self.test_file_suffix_pattern: str = test_file_suffix_pattern or ""
        self.version_pattern: str = version_pattern

    def get_default_ver(self, path) -> Optional[str]:
        fullpath = path
        if os.path.isfile(fullpath):
            # this is to get the version number
            line = subprocess.check_output([fullpath, '--version'], stderr=subprocess.STDOUT)
            if match := re.search(self.version_pattern, line.decode()):
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
        if not self.found:
            root = ToolInfo.get_root(self, None)
            self.scan_query(root)
        if self.found:
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
        if ret and self.found:
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
        if root_path:
            found = self.scan_query(root_path, False)
        elif SCons.Util.is_String(use_script):
            found = {'0.0.0': (None, None)}
        else:
            # use our build in lookup logic
            root = ToolInfo.get_root(self, None)
            found = self.scan_query(root)

        if not found:
            return None

        ret: dict = {}
        for v, p in found.items():
            if tmp := self.exists(env, namespace, v, p[0], use_script, p[1]):
                ret.update(self.make_ver_shell_env_set(v, tmp))

        return ret

    def scan_query(self, install_root: Optional[str], opt_scan: bool=True):
        found: dict = {}

        def set_found_tuple(path, item):
            nonlocal found
            pathwtool = os.path.join(path, item)
            if version := self.get_default_ver(pathwtool):
                api.output._trace_msgf(['gnu_info', "tool_info"], f"query scan found[{version}] = ({path}, {pathwtool})")
                found[version] = (path, pathwtool)

        if not self.found:
            test_file_pattern = re.compile(self.test_file_prefix_pattern + self.test_file.replace('+', r'\+') + self.test_file_suffix_pattern, re.IGNORECASE)
            if opt_scan:
                opt_dir_pattern = test_file_pattern if not self.opt_pattern else re.compile(self.opt_pattern, re.IGNORECASE)
                # see if we can find a version in the optional directories provided
                # based on pattern of either:
                #   * dir/tool
                #   * dir/tool-ver/bin/tool
                # this can be /opt or any other user provided directory
                for d in self.opt_paths:
                    # check that is exists and is directory
                    if os.path.isdir(d):
                        api.output.verbose_msgf(['gnu_info', "tool_info"], f"query scan opt_root={d}")
                        for item in os.listdir(d):
                            # look for file match
                            if self.test_file == item or test_file_pattern.fullmatch(item):
                                set_found_tuple(d, item)
                            # look for all directories here that match pattern
                            if opt_dir_pattern.match(item):
                                fullpath = os.path.join(d, item, 'bin')
                                if not os.path.exists(fullpath):
                                    continue
                                api.output.verbose_msgf(['gnu_info', "tool_info"], f"query scan opt_root={fullpath}")
                                for fitem in os.listdir(fullpath):
                                    if self.test_file == fitem or test_file_pattern.fullmatch(fitem):
                                        set_found_tuple(fullpath, fitem)

            if install_root:
                api.output.verbose_msgf(['gnu_info', "tool_info"], f"query scan install_root={install_root}")

                # see if in this area we have any possible matches of different versions
                # using a convention of [prefix]-tool-[suffix]. By default we look for
                # tool and tool-suffix. For example, `gcc`, `gcc-14`, `clang-15.2`
                # overrides anything discovered in opt_scan
                for item in os.listdir(install_root):
                    if self.test_file == item or test_file_pattern.fullmatch(item):
                        set_found_tuple(install_root, item)

                # see if we can find a default version in the directories provided
                # overrides any previous finds of same version
                api.output.trace_msgf(['gnu_info', "tool_info"], f"query scan install_root priority override")
                set_found_tuple(install_root, self.test_file)

            self.found = found

        if not self.found:
            api.output.verbose_msgf(['gnu_info', "tool_info"], "Nothing was found!")
            return None
        api.output.verbose_msgf(['gnu_info', "tool_info"], f"Found:\n{pprint.pformat(found)}")
        return self.found


gxx = ToolSetting('gxx')
gcc = ToolSetting('gcc')
clang = ToolSetting('clang')
binutils = ToolSetting('binutils')
emsdk = ToolSetting('emsdk')
cmake = ToolSetting('cmake')
