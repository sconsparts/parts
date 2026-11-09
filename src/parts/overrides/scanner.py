'''
this code is called by SCons to work around a "bug" with the scanner in how it uses the subst() API
The primary issue is that scanner often try to get a list value based variable it wants to expand,
because the subst code at the moment does not allow for an item to expand it no more than one item, it
gets back some string like "foo.a boo.a" not "foo.a" and "boo.a" which means that scanner will fail to find
the item it is scanning for and fail to set a dependency as needed. Since Parts requires the need for the
subst to possibly process more than one item, and the currently the scanner tend to subst() each item in
the list separately, we "pre expand the values" to allow the scanner to work as expected. This also give us a small
speed boost as we fill in the values as at this point it is not going to change. This prevents extra subst()
processing later on the same environment for the same variable.
'''


#import _thread

#import parts.glb as glb
#import parts.mappers as mappers
#import parts.node_helpers as node_helpers
#import parts.core.builders as builders
import parts.core.util as common
import SCons.Scanner
import SCons.Tool


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

def path_reduce(self, env, dir=None, target=None, source=None):
    '''
    because of quirks the paths in certain cases can get huge with common values
    This reduce the value to just needed paths
    This is mostly for the "old" logic as we cannot reduce as we might like to
    '''
    return tuple(common.make_unique(self.orig_path(env, dir, target, source)))

SCons.Scanner.ScannerBase.orig_path=SCons.Scanner.ScannerBase.path
SCons.Scanner.ScannerBase.path = path_reduce


class _IncludeAndSystemIncludeDirs:
    '''
    The C scanner's path function: the CPPPATH directories, then the
    SYSCPPPATH ones. A directory in both lists is searched only at its
    SYSCPPPATH position, as gcc and clang ignore -I for a directory that is
    also given with -isystem.
    '''

    def __init__(self):
        self._include = SCons.Scanner.FindPathDirs('CPPPATH')
        self._system = SCons.Scanner.FindPathDirs('SYSCPPPATH')

    def __call__(self, env, dir=None, target=None, source=None, argument=None):
        system = self._system(env, dir, target, source, argument)
        include = tuple(d for d in self._include(env, dir, target, source, argument) if d not in system)
        return include + system


# A C/C++ source finds headers through CPPPATH and, for a dependency declared
# with system=True, through SYSCPPPATH, which the cc and c++ tools pass after
# CPPPATH ($_CPPSYSINCFLAGS after $_CPPINCFLAGS in _CCCOMCOM), as -isystem on
# gcc and clang. SCons' default C scanner searches only CPPPATH, so a header
# found through SYSCPPPATH was never a dependency of the object, and changing
# it rebuilt nothing. Have that scanner search both, in the compile line's
# order. An empty or unset SYSCPPPATH adds no directories. Only the default
# C scanner (SCons.Tool.CScanner) is changed; a project that installs its own,
# such as SCons' CConditionalScanner, still searches CPPPATH alone.
SCons.Tool.CScanner.path_function = _IncludeAndSystemIncludeDirs()

# def wrap_FindPathDirs(klass):
#     def _call(self, env, dir, target=None, source=None, argument=None):
#         pass
#     try:
#         func = klass.__call__.__func__
#     except Exception:
#         func = klass.__call__
#     _call.__code__ = func.__code__

#     def call(self, env, dir, target=None, source=None, argument=None):
#         global _call
#         prop_lst = env.get(self.variable)
#         if prop_lst:
#             mappers.sub_lst(env, prop_lst, _thread.get_ident(), recurse=False)
#         return _call(self, env, dir, target, source, argument)

#     func.__code__ = call.__code__
#     func.__globals__.update(
#         _call=_call,
#         mappers=mappers,
#         _thread=_thread,
#     )


# wrap_FindPathDirs(SCons.Scanner.FindPathDirs)

# vim: set et ts=4 sw=4 ai :
