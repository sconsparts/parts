'''
this file provides the AbsFile wrappers. I have not moved this to pieces area
yet as i need a way to safely add the global object to parts export statement
'''

import glb
import common
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
        if __debug__: logInstanceCreation(self)
        self.timestamp=0
        self.csig=0

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


class _AbsFile(object):
    def __init__(self,env):
        if __debug__: logInstanceCreation(self)
        self.env=env
    def __call__(self, path):
        return abs_path(self.env, path, self.env.File)

class _AbsDir(object):
    def __init__(self,env):
        if __debug__: logInstanceCreation(self)
        self.env=env
    def __call__(self,path):
        return abs_path(self.env, path, self.env.Dir)

def AbsFile(env, path):
    return abs_path(env, path, env.File)

def AbsDir(env, path):
    return abs_path(env, path, env.Dir)

# import the meta object we will need to add our code to as methods
from SCons.Script.SConscript import SConsEnvironment

#add as global to part scope
api.register.add_global_parts_object('AbsFile',_AbsFile,True)
api.register.add_global_parts_object('AbsDir',_AbsDir,True)

# adding logic to Scons Enviroment object
SConsEnvironment.AbsFile=AbsFile
SConsEnvironment.AbsDir=AbsDir

