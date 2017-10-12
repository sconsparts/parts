'''
this file provides the AbsFile wrappers. I have not moved this to pieces area
yet as i need a way to safely add the global object to parts export statement
'''

import glb
import common
import core.util as util
import api.output
import metatag
import ctypes
import exceptions

import SCons.Script
import SCons.Util
import SCons.Node.FS

import os

from SCons.Debug import logInstanceCreation


class ninfotmp(object):

    def __init__(self):
        if __debug__:
            logInstanceCreation(self)
        self.timestamp = 0
        self.csig = 0


def node_up_to_date(node):
    '''
    Expects a SCons node object, will test against stored info
    to see if it is uptodate
    '''

    node = glb.engine.def_env.arg2nodes(node)[0]
    ninfo = node.get_stored_info().ninfo
    return not node.changed_timestamp_then_content(node, ninfo)


def abs_path(env, path, create_node):
    path = env.subst(path)
    if path.startswith('#'):
        directory = env.Dir('#')
        path = path[len('#'):]
    else:
        directory = env.Dir(env['SRC_DIR'])
    result = create_node(path, directory)
    return result.srcnode().abspath


def abs_path_node(env, path, create_node):
    path = env.subst(path)
    scons_dir = env.Dir('#')
    directory = env.Dir('$SRC_DIR')
    result = create_node(path, directory)
    if result.is_under(directory):
        # this is under the current parts
        return create_node(directory.rel_path(result))
    elif result.is_under(scons_dir):
        # this is under the SConstruct root
        path = '$OUTOFTREE_BUILD_DIR/' + scons_dir.rel_path(result)
        return create_node(path)
    # it is not under the Sconstruct directory
    # we base this off the root directory
    # on windows we need to check for volumes other than C:
    path = result.abspath
    # looks like window path that is not c:\
    if path[1] == ":" and result.abspath[0] != 'C':
        # return path, we cannot map this to a variant directory
        return create_node(result.srcnode().abspath)
    # map to a variant directory
    path = '$ROOT_BUILD_DIR' + path[2:]
    return create_node(path)


# these provide a string Absolute path
class _AbsFile(object):

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, path):
        return abs_path(self.env, path, self.env.File)


class _AbsDir(object):

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, path):
        return abs_path(self.env, path, self.env.Dir)


def AbsFile(env, path):
    return abs_path(env, path, env.File)


def AbsDir(env, path):
    return abs_path(env, path, env.Dir)

# these provide a Node that might be tweak to work with
# the Variant Directory of the given Part


class _AbsFileNode(object):

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, path):
        return abs_path_node(self.env, path, self.env.File)


class _AbsDirNode(object):

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, path):
        return abs_path_node(self.env, path, self.env.Dir)


def AbsFileNode(env, path):
    return abs_path_node(env, path, env.File)


def AbsDirNode(env, path):
    return abs_path_node(env, path, env.Dir)


# import the meta object we will need to add our code to as methods
from SCons.Script.SConscript import SConsEnvironment

# add as global to part scope
api.register.add_global_parts_object('AbsFile', _AbsFile, True)
api.register.add_global_parts_object('AbsDir', _AbsDir, True)
api.register.add_global_parts_object('AbsFileNode', _AbsFileNode, True)
api.register.add_global_parts_object('AbsDirNode', _AbsDirNode, True)

# adding logic to Scons Enviroment object
SConsEnvironment.AbsFile = AbsFile
SConsEnvironment.AbsDir = AbsDir
SConsEnvironment.AbsFileNode = AbsFileNode
SConsEnvironment.AbsDirNode = AbsDirNode
