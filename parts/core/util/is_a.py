import SCons.Util
import SCons.Node


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


def isDictionary(obj):
    return SCons.Util.is_Dict(obj)


def isString(obj):
    return isinstance(obj, basestring) or SCons.Util.is_String(obj)


def isBool(obj):
    return isinstance(obj, bool)


def isInt(obj):
    return isinstance(obj, int)


def isFloat(obj):
    return isinstance(obj, float)
