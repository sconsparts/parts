

import os
import re
import sys

import parts.api as api
import parts.mappers as mappers
import parts.tools.Common.Finders as Finders
import parts.version as version
from SCons.Debug import logInstanceCreation

from . import common

# android scanner for Windows


class win_scanner:

    def __init__(self, env, arch, tool_prefix, tool):
        if __debug__:
            logInstanceCreation(self)
        self.arch = arch
        self.env_var = Finders.EnvFinder(env)
        self.tool_prefix = tool_prefix
        self.tool = tool
        self.cache = None

    def scan(self):
        # search for all known location for a give version
        if self.cache is None:
            # what we will want to return
            ret = {}
            # we will scan for three possible locations
            # being a home directory,program files and c drive
            # we will also look at an environment variable NDK_ROOT
            ndk_root = self.env_var()
            paths = [os.path.expanduser('~'), r'C:\Program Files (x86)\Android', r'C:\Program Files\Android', "c:\\", "\\"]
            if ndk_root:
                paths = [ndk_root] + paths

            for path in paths:
                path = os.path.abspath(path)
                if not os.path.isdir(path):
                    continue
                for item0 in os.listdir(path):
                    if item0.lower().startswith("android-ndk-") or ndk_root == path:
                        if ndk_root == path:
                            ndk_path = ndk_root
                        else:
                            ndk_path = os.path.join(path, item0)
                        temp = os.path.join(ndk_path, 'toolchains')

                        # we check to get the version of the compiler
                        # we assume that a given NDK comes with one version of the toolchain
                        # not two versions
                        if os.path.exists(temp) == False:
                            continue
                        version = None
                        archpath = None
                        for item1 in os.listdir(temp):
                            fullpath = os.path.join(temp, item1)
                            if os.path.isdir(fullpath):
                                # if this is a directory
                                if item1.startswith(self.arch):
                                    version = item1.split("-")[-1]
                                    archpath = item1
                                    toolpath = os.path.join(ndk_path, 'toolchains', archpath,
                                                            r'prebuilt\windows{0}\bin', self.tool_prefix + self.tool)
                                    for arch in ('', '-x86_64'):
                                        if os.path.isfile(toolpath.format(arch)):
                                            # we have a hit. store important data
                                            ret[version] = ndk_path
                                            break

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

# android scanner for posix/mac


class posix_scanner:
    if sys.platform == 'linux2':
        host = 'linux'
    elif sys.platform == 'darwin':
        host = 'darwin'

    def __init__(self, env, arch, tool_prefix, tool):
        if __debug__:
            logInstanceCreation(self)
        self.arch = arch
        self.env_var = Finders.EnvFinder(env)
        self.tool_prefix = tool_prefix
        self.tool = tool
        self.cache = None

    def scan(self):
        # search for all known location for a give version
        if self.cache is None:
            # what we will want to return
            ret = {}
            # we will scan for three possible locations
            # being a home directory,program files and c drive
            # we will also look at an environment variable NDK_ROOT
            ndk_root = self.env_var()
            # need to relook at the default paths for posix/mac systems
            paths = [os.path.expanduser('~'),
                     os.path.expanduser('~') + '/Android',
                     os.path.expanduser('~') + '/android',
                     '/opt', '/opt/Android',
                     '/opt/android',
                     "/",
                     "/Android",
                     "/android"]

            if ndk_root:
                paths = [ndk_root] + paths

            for path in paths:
                if not os.path.isdir(path):
                    continue
                for item0 in os.listdir(path):
                    if item0.lower().startswith("android-ndk-") or ndk_root == path:
                        if ndk_root == path:
                            ndk_path = ndk_root
                        else:
                            ndk_path = os.path.join(path, item0)
                        temp = os.path.join(ndk_path, 'toolchains')

                        # we check to get the version of the compilers
                        if os.path.exists(temp) == False:
                            continue
                        version = None
                        archpath = None
                        for item1 in os.listdir(temp):
                            fullpath = os.path.join(temp, item1)
                            if os.path.isdir(fullpath):
                                # if this is a directory
                                if item1.startswith(self.arch):
                                    version = item1.split("-")[-1]
                                    archpath = item1
                                    toolpath = os.path.join(ndk_path, 'toolchains', archpath, r'prebuilt/' +
                                                            self.host + '-{0}/bin', self.tool_prefix + self.tool)
                                    for arch in ('x86', 'x86_64'):
                                        if os.path.isfile(toolpath.format(arch)):
                                            # we have a hit. store important data
                                            ret[version] = ndk_path
                                            break
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


# this is a mapper to get the lastest API for android in the given NDK
LATEST_PLATFROM_VERSIONS = dict()


def GetLatestNDKAPI(path):
    try:
        return LATEST_PLATFROM_VERSIONS[path]
    except KeyError:
        versions = [version.version(p.split('-')[1]) for p in os.listdir(
            os.sep.join((path, 'platforms'))) if '-' in p]
        LATEST_PLATFROM_VERSIONS[path] = result = versions and str(max(versions)) or ""
        return result


# mapping table for differnt STL types in android SDK
android_stl_map_x86 = {
    'system': {'CPPPATH':
               ['${GXX.INSTALL_ROOT}/sources/cxx-stl/system/include'],
               },
    'gabi++_static': {'CPPPATH':
                      ['${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/include'],
                      'LIBPATH': ["${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/libs/${TARGET_ARCH}"],
                      'LIBS': ['libgabi++_static.a']},
    'gabi++_shared': {'CPPPATH':
                      ['${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/include'],
                      'LIBPATH': ["${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/libs/${TARGET_ARCH}"],
                      'LIBS': ['libgabi++_shared']},
    'stlport_static': {'CPPPATH':
                       ['${GXX.INSTALL_ROOT}/sources/cxx-stl/stlport/stlport',
                        '${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/include'],
                       'CPPDEFINES': ['_GNU_SOURCE'],
                       'CXXFLAGS': ['-fuse-cxa-atexit'],
                       'LIBPATH': ["${GXX.INSTALL_ROOT}/sources/cxx-stl/stlport/libs/${TARGET_ARCH}"],
                       'LIBS': ['libstlport_static.a']},
    'stlport_shared': {'CPPPATH':
                       ['${GXX.INSTALL_ROOT}/sources/cxx-stl/stlport/stlport',
                        '${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/include'],
                       'CPPDEFINES': ['_GNU_SOURCE'],
                       'CXXFLAGS': ['-fuse-cxa-atexit'],
                       'LIBPATH': ["${GXX.INSTALL_ROOT}/sources/cxx-stl/stlport/libs/${TARGET_ARCH}"],
                       'LIBS': ['libstlport_shared']},
    'gnustl_static': {'CPPPATH':
                      ['${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/include',
                       '${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/include/backward',
                       '${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/libs/${TARGET_ARCH}/include'],
                      'LIBPATH': ["${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/libs/${TARGET_ARCH}"],
                      'LIBS': ['gnustl_static.a']},
    'gnustl_shared': {'CPPPATH':
                      ['${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/include',
                       '${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/include/backward',
                       '${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/libs/${TARGET_ARCH}/include'],
                      'LIBPATH': ["${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/libs/${TARGET_ARCH}"],
                      'LIBS': ['gnustl_shared', 'm']
                      }
}

android_stl_map_x86_pre_r8 = {
    'system': {'CPPPATH':
               ['${GXX.INSTALL_ROOT}/sources/cxx-stl/system/include'],
               },
    'gabi++_static': {'CPPPATH':
                      ['${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/include'],
                      'LIBPATH': ["${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/libs/${TARGET_ARCH}"],
                      'LIBS': ['libgabi++_static.a']},
    'gabi++_shared': {'CPPPATH':
                      ['${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/include'],
                      'LIBPATH': ["${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/libs/${TARGET_ARCH}"],
                      'LIBS': ['libgabi++_shared']},
    'stlport_static': {'CPPPATH':
                       ['${GXX.INSTALL_ROOT}/sources/cxx-stl/stlport/stlport',
                        '${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/include'],
                       'CPPDEFINES': ['_GNU_SOURCE'],
                       'CXXFLAGS': ['-fuse-cxa-atexit'],
                       'LIBPATH': ["${GXX.INSTALL_ROOT}/sources/cxx-stl/stlport/libs/${TARGET_ARCH}"],
                       'LIBS': ['libstlport_static.a']},
    'stlport_shared': {'CPPPATH':
                       ['${GXX.INSTALL_ROOT}/sources/cxx-stl/stlport/stlport',
                        '${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/include'],
                       'CPPDEFINES': ['_GNU_SOURCE'],
                       'CXXFLAGS': ['-fuse-cxa-atexit'],
                       'LIBPATH': ["${GXX.INSTALL_ROOT}/sources/cxx-stl/stlport/libs/${TARGET_ARCH}"],
                       'LIBS': ['libstlport_shared']},
    'gnustl_static': {'CPPPATH':
                      ['${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/include',
                       r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/include/backward',
                       r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/libs/${TARGET_ARCH}/include'],
                      'LIBPATH': ["${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/libs/${TARGET_ARCH}"],
                      'LIBS': ['gnustl_static.a']},
    'gnustl_shared': {'CPPPATH':
                      ['${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/include',
                       r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/include/backward',
                       r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/libs/${TARGET_ARCH}/include'],
                      'LIBPATH': ["${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/libs/${TARGET_ARCH}"],
                      'LIBS': ['gnustl_shared', 'm']
                      }
}

android_stl_map_arm = {
    'system': {'CPPPATH':
               ['${GXX.INSTALL_ROOT}/sources/cxx-stl/system/include'],
               },
    'gabi++_static': {'CPPPATH':
                      ['${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/include'],
                      'LIBPATH': ["${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/libs/armeabi"],
                      'LIBS': ['libgabi++_static.a']},
    'gabi++_shared': {'CPPPATH':
                      ['${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/include'],
                      'LIBPATH': ["${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/libs/armeabi"],
                      'LIBS': ['libgabi++_shared']},
    'stlport_static': {'CPPPATH':
                       ['${GXX.INSTALL_ROOT}/sources/cxx-stl/stlport/stlport',
                        '${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/include'],
                       'CPPDEFINES': ['_GNU_SOURCE'],
                       'CXXFLAGS': ['-fuse-cxa-atexit'],
                       'LIBPATH': ["${GXX.INSTALL_ROOT}/sources/cxx-stl/stlport/libs/armeabi"],
                       'LIBS': ['libstlport_static.a']},
    'stlport_shared': {'CPPPATH':
                       ['${GXX.INSTALL_ROOT}/sources/cxx-stl/stlport/stlport',
                        '${GXX.INSTALL_ROOT}/sources/cxx-stl/gabi++/include'],
                       'CPPDEFINES': ['_GNU_SOURCE'],
                       'CXXFLAGS': ['-fuse-cxa-atexit'],
                       'LIBPATH': ["${GXX.INSTALL_ROOT}/sources/cxx-stl/stlport/libs/armeabi"],
                       'LIBS': ['libstlport_shared']},
    'gnustl_static': {'CPPPATH':
                      ['${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/include',
                       r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/include/backward',
                       r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/libs/armeabi/include'],
                      'LIBPATH': ['${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/libs/armeabi'],
                      'LIBS': ['gnustl_static.a']},
    'gnustl_shared': {'CPPPATH':
                      ['${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/include',
                       r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/include/backward',
                       r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/libs/armeabi/include'],
                      'LIBPATH': ['${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/libs/armeabi'],
                      'LIBS': ['gnustl_shared']
                      }
}

# mapper for STL data


class android_stl_mapper(mappers.mapper):
    ''' This class maps Androidn path based on the user selection for which STL library to use
    '''
    name = '_ANDROID_STL'

    def __init__(self, key):
        self.key = key

    def __call__(self, target, source, env, for_signature):
        stl_map = env['GXX']['STL_MAP']
        tmp = env.get("ANDROID_STL_MAP", {})
        stl_map.update(tmp)
        stl_type = env.get("ANDROID_STL")
        if stl_type in stl_map:
            # get data to map
            data = stl_map[stl_type].get(self.key, [''])
            # map data in to the environment
            self.map_global_var(env, self.key, "${{{0}('{1}')}}".format(self.name, self.key), data, " ")
            return data[0]
        else:
            # we have a bad key .. report it
            pass
        return ""


api.register.add_mapper(android_stl_mapper)
