'''
this code is called by SCons to work around a "bug" with the scanner in how it uses the subst() API
The primary issue is that scanner often try to get a list value based variable it wants to expand,
because the subst code at the moment does not allow for an item to expand it no more than one item, it
gets back some string like "foo.a boo.a" not "foo.a" and "boo.a" which means that scanner will fail to find
the item it is scanning for and fail to set a dependancy as needed. Since Parts requires the need for the
subst to posilbly process more than one item, and the currently the scanner tend to subst() each item in
the list seperatly, we "pre expand the values" to allow the scanner to work as expected. This also give us a small
speed boost as we fill in the values as at this point it is not going to change. This prevents extra subst()
processing later on the same environment for the same variable.
'''


import _thread

import parts.glb as glb
import parts.mappers as mappers
import parts.node_helpers as node_helpers
import parts.core.builders as builders
import SCons.Scanner


def wrap_Prog_scan(func):
    def _scan(node, env, libpath=()):
        pass
    _scan.__code__ = func.__code__
    _scan.__globals__.update(**func.__globals__)

    def scan(node, env, libpath=()):
        global _scan
        if not 'LIBS' in env and not 'LIBEXS' in env:
            return []
        return _scan(node, env.Override(dict(LIBS=env.get('LIBS', []) + env.get('LIBEXS', []))), libpath)
    func.__code__ = scan.__code__
    func.__globals__.update(_scan=_scan)


wrap_Prog_scan(SCons.Scanner.Prog.scan)


def wrap_FindPathDirs(klass):
    def _call(self, env, dir, target=None, source=None, argument=None):
        pass
    try:
        func = klass.__call__.__func__
    except Exception:
        func = klass.__call__
    _call.__code__ = func.__code__

    def call(self, env, dir, target=None, source=None, argument=None):
        global _call
        prop_lst = env.get(self.variable)
        if prop_lst:
            mappers.sub_lst(env, prop_lst, _thread.get_ident(), recurse=False)
        return _call(self, env, dir, target, source, argument)

    func.__code__ = call.__code__
    func.__globals__.update(
        _call=_call,
        mappers=mappers,
        _thread=_thread,
    )


# wrap_FindPathDirs(SCons.Scanner.FindPathDirs)

# vim: set et ts=4 sw=4 ai :
