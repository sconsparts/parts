from __future__ import absolute_import, division, print_function

from future.utils import native_str

import SCons.Node
import SCons.Util


def isNode(obj):
    return isinstance(obj, (SCons.Node.Alias.Alias, SCons.Node.FS.Entry, SCons.Node.FS.Dir, SCons.Node.FS.File, SCons.Node.FS.FileSymbolicLink, SCons.Node.Python.Value))


def isEntry(obj):
    return isinstance(obj, SCons.Node.FS.Entry)


def isDir(obj):
    return isinstance(obj, SCons.Node.FS.Dir)


def isFile(obj):
    return isinstance(obj, SCons.Node.FS.File)


def isValue(obj):
    return isinstance(obj, SCons.Node.Python.Value)


def isAlias(obj):
    return isinstance(obj, SCons.Node.Alias.Alias)


def isSymLink(obj):
    return isinstance(obj, SCons.Node.FS.FileSymbolicLink)


def isList(obj):
    return SCons.Util.is_List(obj)


def isSet(obj):
    return isinstance(obj, set)


def isDictionary(obj):
    return SCons.Util.is_Dict(obj)


def isTuple(obj):
    return isinstance(obj, tuple)


def isString(obj):
    return isinstance(obj, native_str) or SCons.Util.is_String(obj)


def isBool(obj):
    return isinstance(obj, bool)


def isInt(obj):
    return isinstance(obj, int)


def isFloat(obj):
    return isinstance(obj, float)
