'''
this file contains pattern which is used to select file on disk based on simple
matching expressions. Scons just add a Glob function.. need to consider using that
internal here instead, and then possiblely removing pattern 100%
'''


import os
from typing import List, Union

import SCons.Script
from SCons.Debug import logInstanceCreation
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

import parts.api as api
import parts.common as common
import parts.core.util as util
# patterns
import parts.glb as glb


def Pattern_func(env: SConsEnvironment, src_dir: str = '', includes: Union[str, List[str]] = '*',
                 excludes: Union[str, List[str]] = '', recursive: bool = True):
    return Pattern(src_dir, includes, excludes, recursive, env)


g_db = {}


class Pattern:
    def __init__(self, src_dir: str = './', includes: Union[str, List[str]] = ['*'],
                 excludes: Union[str, List[str]] = [], recursive: bool = True, env: SConsEnvironment = None):
        if env is None:
            env = glb.engine.def_env
        self._env = env

        if __debug__:
            logInstanceCreation(self)
        if util.isString(src_dir) and src_dir.startswith(('../','#')):
            self.src_dir = env.AbsDirNode(src_dir)
        else:
            self.src_dir = env.Dir(src_dir)

        self.includes = []
        includes = common.make_list(includes)
        for i in includes:
            self.includes.append(os.path.normpath(i))

        self.excludes = []
        includes = common.make_list(excludes)
        for i in excludes:
            if i != '*':
                self.excludes.append(os.path.normpath(i))

        self.recursive = recursive
        self.map = None

    def files(self, directory=None):
        '''
        return the files found by the pattern
        '''

        if self.map is None:
            self.generate()
        if directory is None:
            fl = []
            root_path = SCons.Script.Dir('.').srcnode().abspath
            if not self.src_dir.abspath.startswith(root_path):
                root_path = self.src_dir.abspath
            for root_dir, src_nodes in self.map.items():
                for node in src_nodes:
                    fl.append(node)
            # to help with sig generations
            fl.sort(key=lambda x: x.ID)
            return fl

        return self.map[directory]

    def sub_dirs(self):
        if self.map is None:
            self.generate()
        return list(self.map.keys())

    def target_source(self, root_target):
        src_list = []
        trg_list = []
        root_target = self._env.arg2nodes(root_target, self._env.fs.Dir)[0]
        if self.map is None:
            self.generate()
        for dnode, slist in list(self.map.items()):
            for node in slist:
                if util.isSymLink(node):
                    target_node = root_target.FileSymbolicLink(self.src_dir.rel_path(node))
                else:
                    target_node = root_target.File(self.src_dir.rel_path(node))
                trg_list.append(target_node)
                src_list.append(node)

        return (trg_list, src_list)

    def generate(self, exclude_path=''):
        '''
        do a recursive glob
        '''
        m = {}
        # create base path
        paths = [self.src_dir]
        # there is a quirk in which Glob() does some odd behavior when we scan a variant directory
        # This is to protect us from recursing down the variant directory more than once
        guard_path = f"{self.src_dir.ID}/{self._env.Dir('$BUILD_DIR_ROOT').name}"

        for path in paths:
            objs = path.glob(".*")
            objs += path.glob("*")
            for entity in objs:
                is_dir = util.isDir(entity)
                # __rt and __oot are funny files that are out of tree
                # # or under the SConstruct but not the parts file
                if is_dir:
                    if entity.name not in ["__rt", "__oot", ".parts.cache"] and guard_path not in path.ID and self.recursive:
                        paths.append(entity)
                        continue
                    else:
                        continue

                matches = common.matches(self.src_dir.rel_path(entity), self.includes, self.excludes)
                if matches:
                    api.output.verbose_msgf(["pattern.add", "pattern"], "Adding {0} {1}", path, entity.ID)
                    try:
                        m[path].append(entity)
                    except KeyError:
                        m[path] = [entity]
                else:
                    api.output.verbose_msgf(["pattern.skip", "pattern"], "Skipped {0}", entity.ID)
        self.map = m


class _Pattern:
    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, src_dir: str = '', includes: Union[str, List[str]] = ['*'],
                 excludes: Union[str, List[str]] = [], recursive: bool = True):
        return Pattern(src_dir=src_dir, includes=includes, excludes=excludes, recursive=recursive, env=self.env)


# adding logic to Scons Environment object
SConsEnvironment.Pattern = Pattern_func

api.register.add_global_object('Pattern', _Pattern)
api.register.add_global_parts_object('Pattern', _Pattern, True)
