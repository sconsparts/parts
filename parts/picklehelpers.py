try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

UnpicklingError, PicklingError = pickle.UnpicklingError, pickle.PicklingError

import SCons.Node.FS
import SCons.Node.Alias


def persistent_id(obj):
    global class_names
    while True:
        try:
            return '\0'.join((class_names[type(obj)], obj.abspath))
        except KeyError:
            return None
        except NameError:
            class_names = {
                SCons.Node.Alias.Alias: 'SCons.Node.Alias.Alias',
                SCons.Node.FS.Entry: 'SCons.Node.FS.Entry',
                SCons.Node.FS.File: 'SCons.Node.FS.File',
                SCons.Node.FS.Dir: 'SCons.Node.FS.Dir',
                SCons.Node.FS.FileSymbolicLink: 'SCons.Node.FS.FileSymbolicLink',
            }


def dumps(obj, protocol=0):
    result = StringIO.StringIO()
    pickler = pickle.Pickler(result, protocol=protocol)
    pickler.persistent_id = persistent_id
    pickler.dump(obj)
    return result.getvalue()


def persistent_load(obj_id):
    cls_name, path = obj_id.split('\0')
    global node_factories
    while True:
        try:
            return node_factories[cls_name](path)
        except NameError:
            node_factories = {
                'SCons.Node.Alias.Alias': SCons.Node.Alias.default_ans.Alias,
                'SCons.Node.FS.Entry': SCons.Node.FS.get_default_fs().Entry,
                'SCons.Node.FS.File': SCons.Node.FS.get_default_fs().File,
                'SCons.Node.FS.Dir': SCons.Node.FS.get_default_fs().Dir,
                'SCons.Node.FS.FileSymbolicLink': SCons.Node.FS.get_default_fs().FileSymbolicLink,
            }


def loads(string):
    unpickler = pickle.Unpickler(StringIO.StringIO(string))
    unpickler.persistent_load = persistent_load
    return unpickler.load()

# vim: set et ts=4 sw=4 ai ft=python :
