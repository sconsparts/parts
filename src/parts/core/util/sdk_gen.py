import SCons.Node.FS
from SCons.Debug import logInstanceCreation

from .is_a import isString
from .misc import relpath


# # help objects
# class _make_rel:

#     def __init__(self, lst):
#         if __debug__:
#             logInstanceCreation(self)
#         self.lst = lst

#     def string_it(self, env, path):
#         import parts.pattern as pattern
#         ret = '[ '
#         for i in self.lst:
#             if isinstance(i, SCons.Node.FS.Dir):
#                 ret += "env.Dir('" + relpath(env.Dir(i).srcnode().abspath, path) + "')"
#             elif isinstance(i, pattern.Pattern):
#                 _, sr = i.target_source(path)
#                 inc = []
#                 for s in sr:
#                     inc.append(relpath(s, path).replace('\\', '/'))
#                 s = 'Pattern(src_dir="' + relpath(i.src_dir.abspath, path).replace('\\', '/') + '",includes = ' + str(inc)
#                 if i.sub_dir != '':
#                     s += ",sub_dir='" + str(i.sub_dir) + "'"
#                 s += ")"
#                 ret += s
#             else:
#                 ret += "'" + relpath(env.File(i).srcnode().abspath, path).replace('\\', '/') + "'"
#             ret += ','
#         ret = ret[:-1] + ']'
#         return ret


# class _make_reld:

#     def __init__(self, lst):
#         if __debug__:
#             logInstanceCreation(self)
#         self.lst = lst

#     def string_it(self, env, path):
#         ret = []
#         for i in self.lst:
#             if isinstance(i, SCons.Node.FS.Dir):
#                 ret.append("env.Dir(" + relpath(env.Dir(i).srcnode().abspath, path) + ")")
#             else:
#                 ret.append(relpath(env.Dir(i).srcnode().abspath, path))
#         return str(ret)


# class named_parms:

#     def __init__(self, _kw):
#         if __debug__:
#             logInstanceCreation(self)
#         self.kw = _kw

#     def string_it(self, env, path):
#         ret = ""
#         i = len(self.kw)
#         for k, v in self.kw.items():
#             i = i - 1
#             ret += str(k) + "=" + gen_arg(env, path, v)
#             if i > 0:
#                 ret += ','
#         if ret == '':
#             ret = '**{}'
#         return ret


def gen_arg(env, sdk_path, value):
    ret = ''
    if isinstance(value, _make_rel):
        ret += value.string_it(env, sdk_path)
    elif isinstance(value, _make_reld):
        ret += value.string_it(env, sdk_path)
    elif isinstance(value, named_parms):
        ret += value.string_it(env, sdk_path)
    elif isString(value):
        ret += "'" + env.subst(value) + "'"
    else:
        ret += str(value)
    return ret


def func_gen(env, sdk_path, func, values):
    s = '    env.' + func + '('
    i = len(values)
    for v in values:
        i = i - 1
        s += gen_arg(env, sdk_path, v)
        if i > 0:
            s += ','
    s += ')'
    return s


def map_alias_to_root(pobj, concept, alias_str):
    '''
    Returns a list of Alias nodes.
    Each successor is predecessor's parent. I.e. [node, node.parent, node.parent.parent, ...]
    '''

    alias_str = alias_str.format(concept, "${ALIAS}")
    alias = pobj.Env.Alias(alias_str)

    result = list(alias)
    while pobj.Parent:
        pobj = pobj.Parent
        alias = pobj.Env.Alias(alias_str, alias)
        result.extend(alias)

    return result

# vim: set et ts=4 sw=4 ai ft=python :
