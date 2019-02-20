from __future__ import absolute_import, division, print_function

import os
import re
import subprocess
import sys

import parts.tools.Common.Finders as Finders
import SCons.Util
from parts.common import make_list
from SCons.Debug import logInstanceCreation

from . import common

# for version 12.x


class file_scanner12(object):

    def __init__(self, path, pattern, arch, env):
        if __debug__:
            logInstanceCreation(self)
        self.path = path  # path to scan
        self.pattern = pattern    # pattern to install root
        self.arch = arch
        self.env_var = Finders.EnvFinder(make_list(env), arch)
        self.cache = None

    def scan(self):
        # search for all known location for a give version
        if self.cache is None:
            # what we will want to return
            ret = {}
            # pattern to match on
            reg = re.compile(self.pattern, re.I)
            # interate outer directories for match
            if os.path.exists(self.path):
                for item0 in os.listdir(self.path):
                    fullpath0 = os.path.join(self.path, item0)
                    # if this is a directory
                    if os.path.isdir(fullpath0):
                        # if this is a directory
                        result0 = reg.match(item0)
                        if result0:
                            # this is one possible way to look at the
                            # version number of the compiler
                            # ie the data.update.package form
                            version_group1 = result0.groups()[0] + "." + result0.groups()[-1]
                            # test for the bin directory
                            bin_path = os.path.join(fullpath0, 'bin', self.arch, 'icc')

                            if os.path.exists(bin_path):
                                # this is a valid path..
                                # at this point we want to get the version
                                # compiler thinks it is.
                                pipe = subprocess.Popen(bin_path + ' -v',
                                                        shell=True,
                                                        #stdin = 'devnull',
                                                        stderr=subprocess.STDOUT,
                                                        stdout=subprocess.PIPE)

                                pipe.wait()
                                for line in pipe.stdout:
                                    match = re.search(r'icc\s+version\s+([0-9]+\.[0-9]+\.[0-9]*|[0-9]+\.[0-9]+)', line.decode())

                                    if match:
                                        version_group2 = match.groups()[-1]
                                        try:
                                            int(version_group1)
                                        except ValueError:
                                            pass
                                        else:
                                            ret[version_group1] = fullpath0
                                        ret[version_group2] = fullpath0
                                        break

            if ret == {}:
                # ctest env
                ret = self.env_var()
                if ret is not None:
                    ret[self.ver] = ret
            self.cache = ret
        return self.cache

    def resolve_version(self, version):
        tmp = self.scan()
        if tmp is None:
            return None
        k = list(tmp.keys())
        # k.reverse()
        for i in k:
            if common.MatchVersionNumbers(version, i):
                return i
        return None

    def resolve(self, version):
        tmp = self.scan()
        if tmp is None:
            return None
        k = list(tmp.keys())
        # k.reverse()
        for i in k:
            if common.MatchVersionNumbers(version, i):
                return tmp[i]
        return None


# for version 11.x
class file_scanner11(object):

    def __init__(self, path, pattern, pattern2, arch, env):
        if __debug__:
            logInstanceCreation(self)
        self.path = path
        self.pattern = pattern
        self.pattern2 = pattern2
        self.arch = arch
        self.env_var = Finders.EnvFinder(env, arch)
        self.cache = None

    def scan(self):
        # search for all known location for a give version
        if self.cache is None:
            # what we will want to return
            ret = {}
            # pattern to match on
            reg = re.compile(self.pattern, re.I)
            reg2 = re.compile(self.pattern2, re.I)
            # interate outer directories for match
            if os.path.exists(self.path):
                for item0 in os.listdir(self.path):
                    fullpath0 = os.path.join(self.path, item0)
                    # if this is a directory
                    if os.path.isdir(fullpath0):
                        # if this is a directory
                        result0 = reg.match(item0)
                        # iterate the inner directories
                        for item in os.listdir(fullpath0):
                            fullpath = os.path.join(fullpath0, item)
                            if os.path.isdir(fullpath):
                                result = reg2.match(item)
                                if result:
                                    version = ".".join([item0, item])
                                    ret[version] = fullpath
            if ret == {}:
                # ctest env
                ret = self.env_var()
                if ret is not None:
                    ret[self.ver] = ret
            self.cache = ret
        return self.cache

    def resolve_version(self, version):
        tmp = self.scan()
        if tmp is None:
            return None
        k = list(tmp.keys())
        # k.reverse()
        for i in k:
            if common.MatchVersionNumbers(version, i):
                return i
        return None

    def resolve(self, version):
        tmp = self.scan()
        if tmp is None:
            return None
        k = list(tmp.keys())
        # k.reverse()
        for i in k:
            if common.MatchVersionNumbers(version, i):
                return tmp[i]
        return None


class file_scanner9_10(object):

    def __init__(self, path, pattern, arch, env):
        if __debug__:
            logInstanceCreation(self)
        self.path = path
        self.pattern = pattern
        self.arch = arch
        self.env_var = Finders.EnvFinder(env, arch)
        self.cache = None

    def scan(self):
        # search for all known location for a give version
        if self.cache is None:
            # what we will want to return
            ret = {}
            # pattern to match on
            reg = re.compile(self.pattern, re.I)
            # interate directorys for match
            if os.path.exists(self.path):
                for item in os.listdir(self.path):
                    fullpath = os.path.join(self.path, item)
                    if os.path.isdir(fullpath):
                        result = reg.match(item)
                        if result:
                            version = ".".join(result.groups())
                            ret[version] = fullpath
            if ret == {}:
                # ctest env
                ret = self.env_var()
                if ret is not None:
                    ret[self.ver] = ret
            self.cache = ret
        return self.cache

    def resolve_version(self, version):
        tmp = self.scan()
        if tmp is None:
            return None
        k = list(tmp.keys())
        # k.reverse()
        for i in k:
            if common.MatchVersionNumbers(version, i):
                return i
        return None

    def resolve(self, version):
        tmp = self.scan()
        if tmp is None:
            return None
        k = list(tmp.keys())
        # k.reverse()
        for i in k:
            if common.MatchVersionNumbers(version, i):
                # print version, i
                return tmp[i]
        return None
