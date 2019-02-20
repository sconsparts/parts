from __future__ import absolute_import, division, print_function

import SCons.Util
from SCons.Script.SConscript import SConsEnvironment

# this add Parts bindable support to SCons clone call


def PartsClone(self, tools=[], toolpath=None, parse_flags=None, **kw):
    clone_env = self._orig_Clone(tools, toolpath, parse_flags, **kw)
    #rebind and bindable
    clone_env._bindable_vars = set([])
    if hasattr(self, '_bindable_vars'):
        for i in self._bindable_vars:
            clone_env._bindable_vars.add(i)
            clone_env[i]._rebind(clone_env, i)
    return clone_env


# this code is to fix a clone bug, that has been fixed in newer drop fo SCons
try:
    SCons.Util._semi_deepcopy_inst

    def my_semi_deepcopy(x):
        ''' fixes issues with deepcopy'''
        copier = SCons.Util._semi_deepcopy_dispatch.get(type(x))
        if copier:
            return copier(x)
        else:
            return SCons.Util._semi_deepcopy_inst(x)

    SCons.Util.semi_deepcopy = my_semi_deepcopy
except AttributeError:
    pass


# override Clone to deepcopy bindable objects
SConsEnvironment._orig_Clone = SConsEnvironment.Clone
SConsEnvironment.Clone = PartsClone
