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
import parts.errors as errors
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
        self._stackframe = errors.GetPartStackFrameInfo()

    def files(self, directory=None):
        '''
        return the files found by the pattern
        @param directory Returns nodes to the directory provided
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
            fl.sort()
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
                try:
                    src_dir = node.Dir('.')
                except AttributeError:
                    #src_dir = self._env.Dir(os.path.dirname(node.ID))
                    continue
                if src_dir.is_under(root_target):
                    api.output.error_msg(f"Source node '{node}' is under the target root directory '{root_target}'.\
                        \n This is a sign of a bad Pattern() call that is finding items in a VariantDir() that are target outputs from the Builder call that had been created from a previous build run.\n The Builder:",
                        stackframe=errors.GetPartStackFrameInfo(),
                        exit=False
                        )
                    api.output.error_msg(f"Pattern used for this error:",stackframe=self._stackframe)

                if util.isSymLink(node):
                    target_node = root_target.FileSymbolicLink(self.src_dir.rel_path(node))
                else:
                    target_node = root_target.File(self.src_dir.rel_path(node))
                # Clean this up later is needed.. at the moment .git files seems to be special
                if ".git" in target_node.ID:
                    self._env.Ignore(target_node,node)
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
        api.output.verbose_msgf(["pattern.generate.add", "pattern.generate", "pattern"], "Starting scan of {}", self.src_dir)
        for path in paths:
            objs = path.glob(".*",ondisk=True, source=True, strings=False, exclude=None)
            objs += path.glob("*",ondisk=True, source=True, strings=False, exclude=None)
            for entity in objs:
                is_dir = util.isDir(entity)
                # __rt and __oot are funny files that are out of tree
                # # or under the SConstruct but not the parts file
                # match directories on exclude patterns only as they are not files, no need to match item under the directory
                # if the directory is excluded.
                dir_match = common.matches(self.src_dir.rel_path(entity), "*", self.excludes)
                if is_dir:
                    if dir_match and entity.name not in ["__rt", "__oot", ".parts.cache"] and guard_path not in path.ID and self.recursive:
                        api.output.verbose_msgf(["pattern.generate.add", "pattern.generate", "pattern"], f"Recursing {entity.ID}")
                        paths.append(entity)
                        continue
                    else:
                        continue
                matches = common.matches(self.src_dir.rel_path(entity), self.includes, self.excludes)
                if matches:
                    api.output.verbose_msgf(["pattern.generate.add", "pattern.generate", "pattern"], "Adding {0} {1}", path, entity.ID)
                    try:
                        m[path].append(entity)
                    except KeyError:
                        m[path] = [entity]
                else:
                    api.output.verbose_msgf(["pattern.generate.skip", "pattern.generate", "pattern"], "Skipped {0}", entity.ID)
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
api.register.add_method(Pattern_func, 'Pattern')

api.register.add_global_object('Pattern', _Pattern)
api.register.add_global_parts_object('Pattern', _Pattern, True)
