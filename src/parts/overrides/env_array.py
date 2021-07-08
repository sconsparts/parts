# this handle overrides to the env [] operators


import parts.common as common
import parts.glb as glb
from parts.core import util
from SCons.Script.SConscript import SConsEnvironment


def Parts__setitem__(self, key, val):
    #glb.last_key = (key,val)
    if getattr(self, '_log_keys', False):
        if (key in self) == False:
            pobj = glb.engine._part_manager._from_env(self)
            sec = None
            if pobj:
                sec = pobj.DefiningSection
            if sec and util.isString(val):
                sec.UserEnvDiff[key] = val
    self._orig__setitem__(key, val)
    if isinstance(val, common.bindable):
        try:
            self._bindable_vars.add(key)
        except Exception:
            self._bindable_vars = set([key])
        val._bind(self, key)
    elif key in getattr(self, '_bindable_vars', set([])):
        self._bindable_vars.remove(key)

# not using get at the moment.. however that could change


def Parts__getitem__(self, key):

    tmp = self._orig__getitem__(key)
    if hasattr(tmp, '__eval__'):
        tmp = tmp.__eval__()
        self._orig__setitem__(key, tmp)
    return tmp


# override __setitem__ bind env with bindable objects when set
SConsEnvironment._orig__setitem__ = SConsEnvironment.__setitem__
SConsEnvironment.__setitem__ = Parts__setitem__

SConsEnvironment._orig__getitem__ = SConsEnvironment.__getitem__
SConsEnvironment.__getitem__ = Parts__getitem__
