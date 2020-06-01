
import os
import re
import subprocess
import sys

import parts.api as api


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


class GenericScanner:

    def __init__(self, paths:list, dir_pattern:str, subpaths:list, tool_version_pattern:str, tool:str):        
        self.paths:list = paths  # root paths to scan
        self.subpaths:list = subpaths  # subpaths to look for tool in
        self.dir_pattern = dir_pattern # pattern to install root
        self.tool_pattern = tool_version_pattern # pattern to get version of tool via --version
        self.tool= tool
        self.cache = None

    def scan(self):
        # search for all known location for a give version
        if self.cache is None:
            # what we will want to return
            ret = {}            
            # compile expression for speed
            reg = re.compile(self.dir_pattern, re.I)
            api.output.verbose_msgf(["generic.toolscanner","toolscanner"], "Directory pattern: {}",self.dir_pattern)
            api.output.verbose_msgf(["generic.toolscanner","toolscanner"], "Directory pattern: {}",self.tool_pattern)
            # interate outer directories for match
            for path in self.paths:
                self.test_root(path,ret,reg)
            self.cache = ret
        return self.cache

    def test_root(self,path,results,reg):
        api.output.trace_msgf(["generic.toolscanner","toolscanner"], "testing: {}",path)
        if os.path.exists(path):
            for enity in os.listdir(path):
                fullpath = os.path.join(path, enity)
                # if this is a directory
                api.output.trace_msgf(["generic.toolscanner","toolscanner"], "Testing that it is a Directory: {}",fullpath)
                if os.path.isdir(fullpath):
                    api.output.verbose_msgf(["generic.toolscanner","toolscanner"], "Directory Found: {}",fullpath)
                    # if this is a directory
                    result = reg.match(enity)
                    if result:                        
                        # we have a root match
                        # get the version                        
                        version_path = result.groups()[0]
                        api.output.verbose_msgf(["generic.toolscanner","toolscanner"], "Directory pattern matched: {0} version: {1}",enity,version_path)

                        # test the subpath
                        for subpath in self.subpaths:
                            api.output.trace_msgf(["generic.toolscanner","toolscanner"], "Testing sub path for tool: {}",subpath)
                            bin_path = os.path.join(fullpath, subpath, self.tool)
                            #test for tool None mean nothing found, "" means no version found/matched
                            version = self.get_tool_version(bin_path)
                            if version:
                                api.output.verbose_msgf(["generic.toolscanner","toolscanner"], "Adding: {0} version: {1}",fullpath,version)
                                results[version] = fullpath
                            if version_path and version is not None:
                                api.output.verbose_msgf(["generic.toolscanner","toolscanner"], "Adding: {0} version: {1}",fullpath,version)
                                results[version_path] = fullpath

    def get_tool_version(self,path) -> str:
        api.output.trace_msgf(["generic.toolscanner","toolscanner"], "Testing for tool: {}",path)
        pipe = subprocess.Popen(path + ' --version',
                                shell=True,                                
                                stderr=subprocess.STDOUT,
                                stdout=subprocess.PIPE)

        pipe.wait()
        for line in pipe.stdout:
            match = re.search(self.tool_pattern, line.decode())
            if match:
                version = match.groups()[0]
                api.output.verbose_msgf(["generic.toolscanner","toolscanner"], "Tool pattern matched: {0} version: {1}",path,version)
                return version
        return None

    def resolve_version(self, version):
        tmp = self.scan()
        if tmp is None:
            return None
        k = list(tmp.keys())
        # k.reverse()
        for i in k:
            if MatchVersionNumbers(version, i):
                return i
        return None

    def resolve(self, version):
        tmp = self.scan()
        if tmp is None:
            return None
        k = list(tmp.keys())
        # k.reverse()
        for i in k:
            if MatchVersionNumbers(version, i):
                return tmp[i]
        return None

