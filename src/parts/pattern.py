'''
this file contains pattern which is used to select file on disk based on simple
matching expressions. Scons just add a Glob function.. need to consider using that
internal here instead, and then possiblely removing pattern 100%
'''

from __future__ import absolute_import, division, print_function

import os

import parts.api as api
import parts.common as common
import parts.core.util as util
# patterns
import parts.glb as glb
import SCons.Script
from SCons.Debug import logInstanceCreation
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment


def Pattern_func(env, sub_dir='', src_dir='', includes=['*'], excludes=[], recursive=True):
    return Pattern(sub_dir, src_dir, includes, excludes, recursive, env)


g_db = {}


class Pattern(object):
    def __init__(self, sub_dir=None, src_dir=None, includes=['*'], excludes=[], recursive=True, env=None):
        if env is None:
            env = glb.engine.def_env
        self._env = env

        if __debug__:
            logInstanceCreation(self)
        if src_dir is None:
            self.src_dir = env.Dir("./")
        else:
            self.src_dir = env.Dir(src_dir)

        self.includes = []
        for i in includes:
            self.includes.append(os.path.normpath(i))

        self.excludes = []
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
            if self.src_dir.abspath.startswith(root_path) == False:
                root_path = self.src_dir.abspath
            for root_dir, src_nodes in self.map.items():
                for node in src_nodes:
                    fl.append(node)
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
        for path in paths:
            objs = path.glob(".*")
            objs += path.glob("*")
            for enity in objs:
                is_dir = util.isDir(enity)
                matches = common.matches(self.src_dir.rel_path(enity), self.includes, self.excludes)
                # __rt and __oot are funny files that are out of tree
                # # or under the Sconstruct but not the parts file
                if is_dir and not enity.name in ["__rt", "__oot"] and self.recursive:
                    paths.append(enity)
                elif not is_dir and matches:
                    api.output.verbose_msgf(["pattern.add", "pattern"], "Adding {0} {1}", path, enity.ID)
                    try:
                        m[path].append(enity)
                    except KeyError:
                        m[path] = [enity]
                else:
                    api.output.verbose_msgf(["pattern.skip", "pattern"], "Skipped {0}", enity.ID)
        self.map = m

        # else we ignore the item
        self.map = m


'''
class Pattern(object):

    def __init__(self, sub_dir='', src_dir='', includes=['*'], excludes=[], recursive=True, env=None):
        if __debug__:
            logInstanceCreation(self)
        self.sub_dir = sub_dir
        if env is None:
            env = glb.engine.def_env
        self._env = env
        # this funky logic to make sure we get the path of the source location
        # not the path of the Variant Directory
        self.src_dir = SCons.Script.Dir(
            SCons.Script.Dir('.').srcnode().Dir(
                env.subst(src_dir)
            ).abspath
        )

        # print "Pattern src_dir (srcnode):",self.src_dir.srcnode().abspath
        # print "Pattern src_dir path     :",self.src_dir.abspath
        self.includes = []
        for i in includes:
            self.includes.append(os.path.normpath(i))
        # self.includes=includes
        self.excludes = []
        for i in excludes:
            if i != '*':
                self.excludes.append(os.path.normpath(i))
        # self.excludes=excludes
        self.recursive = recursive
        self.map = None

    def sub_dirs(self):
        if self.map is None:
            self.generate()
        return self.map.keys()

    def files(self, directory=None):
        if self.map is None:
            self.generate()
        if directory is None:
            fl = []
            root_path = SCons.Script.Dir('.').srcnode().abspath
            if self.src_dir.abspath.startswith(root_path) == False:
                root_path = self.src_dir.abspath
            for k, v in self.map.iteritems():
                for f in v:
                    s = common.relpath(os.path.join(k, f), root_path)
                    fl.append(s)

            return fl

        return self.map[directory]

    def target_source(self, root_target):

        src_list = []
        trg_list = []
        if self.map is None:
            self.generate()
        for k, v in self.map.iteritems():
            final_path = os.path.join(root_target, k)
            for f in v:
                trg_list.append(os.path.join(final_path, os.path.split(f)[1]))
                src_list.append(f)

        return (trg_list, src_list)

    # code that originally updated the install tree,
    # but refactored to be more python like.
    # made a matches function that is used in the logic below
    def generate(self, exclude_path=''):
        global g_db
        m = {}
       # create base path
        base_path = self.src_dir.abspath
        l = len(base_path)
        # make list of paths to search
        paths = [base_path]
        for path in paths:

            # for this path get the list of item in it
            # try:
            # try to see if we had scanned this already
            # files=g_db[path]

            # for f in files:
            # if util.isList(f):
            ##                        currpath = os.path.join(path,f[0])
            # paths.append(currpath)
            # continue
            ##                    currpath = os.path.join(path,f)
            ##
            # if common.matches(currpath[l+1:], self.includes, self.excludes):
            # key=os.path.join(self.sub_dir,path[l+1:])
            # try:
            # m[key].append(currpath)
            # except KeyError:
            # m[key]=[currpath]
            # except KeyError:

            g_db[path] = []
            # don't have it.. so make the chache and do the search
            for file in os.listdir(path):
                    # combine the path and the file
                currpath = os.path.join(path, file)

                key = os.path.join(self.sub_dir, path[l + 1:])

                # see if this is really a path
                is_dir = os.path.isdir(currpath)
                if is_dir and self.recursive and file not in ('.svn', '.git', '.hg'):
                    tmp = os.path.split(currpath)
                    g_db[tmp[0]].append([tmp[1]])
                    # if so and we want to recurse, add to paths list
                    el = len(exclude_path)  # should make exclude path a list??
                    if currpath[:el] != exclude_path or el == 0:
                        paths.append(currpath)
                elif is_dir == False and common.matches(currpath[l + 1:], self.includes, self.excludes):
                    # else see if it matches pattern and store if it does
                    tmp = os.path.split(currpath)
                    try:
                        m[key].append(currpath)
                    except KeyError:
                        m[key] = [currpath]
                    g_db[tmp[0]].append(tmp[1])
                else:

                    tmp = os.path.split(currpath)
                    g_db[tmp[0]].append(tmp[1])

            # else we ignore the item
        self.map = m

'''


class _Pattern(object):
    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, sub_dir='', src_dir='', includes=['*'], excludes=[], recursive=True):
        return Pattern(sub_dir=sub_dir, src_dir=src_dir, includes=includes, excludes=excludes, recursive=recursive, env=self.env)


# adding logic to Scons Enviroment object
SConsEnvironment.Pattern = Pattern_func

api.register.add_global_object('Pattern', _Pattern)
api.register.add_global_parts_object('Pattern', _Pattern, True)
