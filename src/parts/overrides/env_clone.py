
from collections import UserDict, UserList, OrderedDict, deque

import SCons.Util
from SCons.Script.SConscript import SConsEnvironment

# fix for drop of 4.5.0 .. can remove this later once we have a new drop.. 
# This is a hot patch to address issues

def patch_semi_deepcopy(obj):
    copier = SCons.Util._semi_deepcopy_dispatch.get(type(obj))
    if copier:
        return copier(obj)

    if hasattr(obj, '__semi_deepcopy__') and callable(obj.__semi_deepcopy__):
        return obj.__semi_deepcopy__()

    if isinstance(obj, UserDict):
        return obj.__class__(SCons.Util.semi_deepcopy_dict(obj))

    if isinstance(obj, (UserList, deque)):
        return obj.__class__(SCons.Util._semi_deepcopy_list(obj))

    return obj

SCons.Util.semi_deepcopy = patch_semi_deepcopy


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

# override Clone to deepcopy bindable objects
SConsEnvironment._orig_Clone = SConsEnvironment.Clone
SConsEnvironment.Clone = PartsClone



