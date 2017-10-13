from .. import glb
from .. import errors
from .. import common
from ..core import util
from .. import api
from .. import datacache
from ..pnode import scons_node_info
from ..pnode import pnode_manager
from .. import metatag
from .. import node_helpers

from SCons.Debug import logInstanceCreation

import SCons.Node
import SCons.Util
from SCons.Util import silent_intern
SCons.Node.NodeList = SCons.Util.NodeList

import itertools
import os
import sys
import hashlib
import pprint
import stat

# Import symlinks to make sure it patches SCons.Node.FS and SCons.Environment before
# we refer it
import symlinks

Node = SCons.Node.Node
File = SCons.Node.FS.File
Dir = SCons.Node.FS.Dir
Entry = SCons.Node.FS.Entry
FileSymbolicLink = SCons.Node.FS.FileSymbolicLink
FSBase = SCons.Node.FS.Base
Value = SCons.Node.Python.Value
Alias = SCons.Node.Alias.Alias


def wrap_MkdirFunc(function):
    def MkdirFunc(target, source, env):
        global BuildError, errno
        target = target[0]
        # there is a case in SCons in which a directory depends on a directory
        # that is many levels deep. For some reason the parent directory is not
        # created correctly. This tests and catches the case by making the parent
        if not target.dir.exists():
            SCons.Node.FS.MkdirFunc([target.dir], source, env)
        if not target.exists():
            try:
                target.fs.mkdir(target.abspath)
            except OSError as error:
                if error.errno == errno.EEXIST:
                    if not target.fs.isdir(target.abspath):
                        raise BuildError(node=target,
                                         errstr=("Cannot create directory when "
                                                 "there is an existing file with the same name"),
                                         filename=target.path, exc_info=error)
                else:
                    raise
        return 0
    function.__code__ = MkdirFunc.__code__
    from SCons.Errors import BuildError
    import errno
    function.__globals__.update(BuildError=BuildError, errno=errno)

wrap_MkdirFunc(SCons.Node.FS.MkdirFunc)


class wrapper(object):

    def __init__(self, binfo, ninfo=None):
        if __debug__:
            logInstanceCreation(self)
        self.binfo = binfo
        self.ninfo = ninfo


class fake_ninfo(object):
    __slots__ = ['timestamp', 'csig', '__weakref__']

    def __init__(self, timestamp, csig):
        if __debug__:
            logInstanceCreation(self)
        self.timestamp = timestamp
        self.csig = csig

Node.make_ninfo_from_dict = lambda self, dict: fake_ninfo(dict.get('timestamp', 0), dict.get('csig', 0))


# as it turns out this testing before Scons maps a Environment to a node is broken
# to fix it we will map the Node Class default function ourself
# other wise it go through a Environment proxy, which can be a NULL class that does nothing
# not we only do this for the File as all other values at the moment
#File.changed_since_last_build = File.changed_timestamp_then_content


# def wrap_FS_store_info(klass):
#    _store_info = klass.store_info
#    def store_info(self):
#        glb.pnodes.StoreNode(self)
#        srcnode = self.srcnode()
#        if not srcnode is self and srcnode.exists():
#            glb.pnodes.StoreNode(srcnode)
#            srcnode.isVisited = True
#        self.isVisited = True
#        return _store_info(self)
#    klass.store_info = store_info
# wrap_FS_store_info(SCons.Node.FS.File)

# def wrap_Alias_store_info(klass):
#    _store_info = klass.store_info
#    def store_info(self):
#        glb.pnodes.StoreAlias(self)
#        self.isVisited = True
#        return _store_info(self)
#    klass.store_info = store_info
# wrap_Alias_store_info(SCons.Node.Alias.Alias)

#############################################
# these are pnode addition

def _get_isVisited(self):
    try:
        return self.attributes._isVisited
    except AttributeError:
        return False


def _set_isVisited(self, value):
    self.attributes._isVisited = value

SCons.Node.Node.isVisited = property(_get_isVisited, _set_isVisited)


def _get_FSID(self):
    try:
        return self.attributes.__FSID
    except AttributeError:
        result = SCons.Node.FS.get_default_fs().Dir('#').rel_path(self)
        if os.path.isabs(result) or result.startswith('..'):
            result = self.abspath
        result = result.replace('\\', '/')
        self.attributes.__FSID = result
        return result


def _get_ValueID(self):
    return "{0}".format(self.value)


def _get_AliasID(self):
    return self.name

SCons.Node.FS.Base.ID = property(_get_FSID)
SCons.Node.Python.Value.ID = property(_get_ValueID)
SCons.Node.Alias.Alias.ID = property(_get_AliasID)


def _my_init(self, name, directory, fs):
    self.orig_init(name, directory, fs)
    # may not be the best way.. but works for the moment
    glb.pnodes.AddNodeToKnown(self)

SCons.Node.FS.Base.orig_init = SCons.Node.FS.Base.__init__
SCons.Node.FS.Base.__init__ = _my_init


def def_FS_Entry___init__(klass):
    orig = klass.__init__

    def __init__(self, name, directory, fs):
        if __debug__:
            logInstanceCreation(self, 'Node.FS.Entry')
        orig(self, name, directory, fs)
    klass.__init__ = __init__
def_FS_Entry___init__(SCons.Node.FS.Entry)


def _my_init(self, value, built_value=None):
    if __debug__:
        logInstanceCreation(self, 'Node.Python.Value')
    self.orig_init(value, built_value)
    # may not be the best way.. but works for the moment
    glb.pnodes.AddNodeToKnown(self)

SCons.Node.Python.Value.orig_init = SCons.Node.Python.Value.__init__
SCons.Node.Python.Value.__init__ = _my_init


def map_alias_stored(obj):
    binfo = glb.pnodes.GetAliasStoredInfo(obj.ID)
    if binfo:
        obj._memo['get_stored_info'] = wrapper(binfo)


def _my_init(self, name):
    if __debug__:
        logInstanceCreation(self, 'Node.Alias.Alias')
    self.orig_init(name)
    # may not be the best way.. but works for the moment
    glb.pnodes.AddAlias(self)
    glb.pnodes.AddNodeToKnown(self)

    if glb.engine.isSconstructLoaded:
        map_alias_stored(self)
    else:
        glb.engine.SConstructLoadedEvent += lambda build_mode: map_alias_stored(self)

SCons.Node.Alias.Alias.orig_init = SCons.Node.Alias.Alias.__init__
SCons.Node.Alias.Alias.__init__ = _my_init

# def override_get_found_includes(klass):
#    def get_found_includes(self, env, scanner, path):
#        """Return the included implicit dependencies in this file.
#        Cache results so we only scan the file once per path
#        regardless of how many times this information is requested.
#        """
#        memo_key = (id(env), id(scanner)) + path
#        try:
#            memo_dict = self._memo['get_found_includes']
#        except KeyError:
#            memo_dict = {}
#            self._memo['get_found_includes'] = memo_dict
#        else:
#            try:
#                return memo_dict[memo_key]
#            except KeyError:
#                pass

#        if scanner:
#            # result = [n.disambiguate() for n in scanner(self, env, path)]
#            result = scanner(self, env, path)
#            result = [N.disambiguate() for N in result]
#        else:
#            result = []

#        memo_dict[memo_key] = result

#        return result
#    klass.get_found_includes = get_found_includes

# override_get_found_includes(SCons.Node.FS.File)

# def override_FileFinder(klass):
#    def find_file(self, filename, paths, verbose=None):
#        """
#        find_file(str, [Dir()]) -> [nodes]

#        filename - a filename to find
#        paths - a list of directory path *nodes* to search in.  Can be
#                represented as a list, a tuple, or a callable that is
#                called with no arguments and returns the list or tuple.

#        returns - the node created from the found file.

#        Find a node corresponding to either a derived file or a file
#        that exists already.

#        Only the first file found is returned, and none is returned
#        if no file is found.
#        """
#        memo_key = self._find_file_key(filename, paths)
#        try:
#            memo_dict = self._memo['find_file']
#        except KeyError:
#            memo_dict = {}
#            self._memo['find_file'] = memo_dict
#        else:
#            try:
#                return memo_dict[memo_key]
#            except KeyError:
#                pass

#        if verbose and not callable(verbose):
#            if not SCons.Util.is_String(verbose):
#                verbose = "find_file"
#            _verbose = u'  %s: ' % verbose
#            verbose = lambda s: sys.stdout.write(_verbose + s)

#        if os.altsep and os.altsep != os.sep:
#            filename = filename.replace(os.altsep, os.sep)

#        filename = SCons.Node.FS._my_normcase(filename)
#        drive, dir = SCons.Node.FS._my_splitdrive(filename)
#        path_components = [x for x in dir.split(os.sep) if x]
#        if not path_components:
#            memo_dict[memo_key] = None
#            return None

#        if drive or dir.startswith(os.sep):
#            # file name specifies absolute path
#            if paths:
#                paths = tuple(path.fs.get_root(drive) for path in paths)
#            else:
#                paths = (SCons.Node.FS.get_default_fs().get_root(drive),)

#        name = path_components.pop(-1)
#        if callable(paths):
#            paths = paths()
#        for path in paths:
#            for entry in path_components:
#                try:
#                    path = path.entries[entry]
#                except KeyError:
#                    path = path.dir_on_disk(entry)
#                    if path is None:
#                        break
#                else:
#                    if isinstance(path, SCons.Node.FS.Dir):
#                        continue
#                    elif isinstance(path, SCons.Node.FS.Entry):
#                        path.must_be_same(SCons.Node.FS.Dir)
#                        continue
#                    else:
#                        break
#            else:
#                if verbose:
#                    verbose("looking for '%s' in '%s' ...\n" % (name, path))
#                result, d = path.srcdir_find_file(name)
#                if result:
#                    if verbose:
#                        verbose("... FOUND '%s' in '%s'\n" % (name, d))
#                    memo_dict[memo_key] = result
#                    return result
#        else:
#            memo_dict[memo_key] = None
#            return None
#    klass.find_file = find_file
# override_FileFinder(SCons.Node.FS.FileFinder)
#SCons.Node.FS.find_file = SCons.Node.FS.FileFinder().find_file

# def get_stored_info_alias(self):
#    return self._memo.get('get_stored_info')

# SCons.Node.Alias.Alias.get_stored_info=get_stored_info_alias


def Stored(self):
    try:
        return self.LoadStoredInfo()
    except errors.LoadStoredError:
        return None


SCons.Node.Node.Stored = property(Stored)


def LoadStoredInfo(self):
    return glb.pnodes.GetStoredNodeInfo(self)

SCons.Node.Node.LoadStoredInfo = LoadStoredInfo


def StoreStoredInfo(self):
    pass

SCons.Node.Node.StoreStoredInfo = StoreStoredInfo


def GenerateStoredInfo(self):

    info = scons_node_info.scons_node_info()
    info.Type = self.__class__
    info.Components = metatag.MetaTagValue(self, 'components', ns='partinfo', default={}).copy()
    for partid, sections in info.Components.iteritems():
        info.Components[partid] = set([sec.ID for sec in sections])

    info.AlwaysBuild = bool(self.always_build)
    if isinstance(self, FSBase):
        try:
            if self.ID != self.srcnode().ID and not self.exists() and self.srcnode().exists():
                info.SrcNodeID = self.srcnode().ID
        except:
            pass

    if self.has_builder() or self.side_effect:
        binfo = self.get_binfo()
        nodes = zip(getattr(binfo, 'bsources', []) + getattr(binfo, 'bdepends', []) + getattr(binfo, 'bimplicit', []),
                    binfo.bsourcesigs + binfo.bdependsigs + binfo.bimplicitsigs)
    else:
        nodes = []

    new_binfo = {}

    for node, ninfo in nodes:
        # some time the node info is a string not a Node object
        try:
            key = node.ID
        except:
            # for some reason SCons will store the Alias "children" values as strings
            # not Nodes. This mean that the children of File nodes may not be normalized to
            # the expected value
            # if the node is not known.. we probally want to swap the
            # os.sep value to a posix forms
            if not glb.pnodes.isKnownNode(node):
                key = node.replace(os.sep, '/')
            else:
                key = node
            node = glb.pnodes.GetNode(key)

        if isinstance(node, SCons.Node.FS.Dir):
            # We do not want nodes to depend on directories
            # we make them depend on the directories contents
            nodes.extend(
                # Don't care about the ninfo. It will be got later.
                (entry, None) for name, entry in node.entries.iteritems()
                if name not in ('.', '..'))
            continue

        elif isinstance(node, FSBase):
            ninfo = node.get_ninfo()

        new_binfo[key] = {
            'timestamp': getattr(ninfo, 'timestamp', 0),
            'csig': getattr(ninfo, 'csig', 0)
        }

    info.SourceInfo = new_binfo

    return info

SCons.Node.Node.GenerateStoredInfo = GenerateStoredInfo

# these are "factories" to allow Parts to recreate the Node from cache latter.


def Scons_fsnode_factory(func, ID=None, *lst, **kw):
    if ID:
        return func(ID, '#')
    else:
        return func(ID, *lst, **kw)


def Scons_node_factory(func, ID=None, *lst, **kw):
    if ID:
        return func(ID)
    else:
        return func(ID, *lst, **kw)


def Scons_alias_node_factory(func, ID=None, *lst, **kw):

    if ID:
        tmp = func(ID)[0]
    else:
        tmp = func(ID, *lst, **kw)[0]
    return tmp

pnode_manager.manager.RegisterNodeType(
    File, lambda x, *lst, **kw: Scons_fsnode_factory(SCons.Script.DefaultEnvironment().File, *lst, **kw))
pnode_manager.manager.RegisterNodeType(
    Dir, lambda x, *lst, **kw: Scons_fsnode_factory(SCons.Script.DefaultEnvironment().Dir, *lst, **kw))
pnode_manager.manager.RegisterNodeType(
    Entry, lambda x, *lst, **kw: Scons_fsnode_factory(SCons.Script.DefaultEnvironment().Entry, *lst, **kw))
pnode_manager.manager.RegisterNodeType(FileSymbolicLink, lambda x, *lst, **
                                       kw: Scons_fsnode_factory(SCons.Script.DefaultEnvironment().FileSymbolicLink, *lst, **kw))
pnode_manager.manager.RegisterNodeType(
    Value, lambda x, *lst, **kw: Scons_node_factory(SCons.Script.DefaultEnvironment().Value, *lst, **kw))
pnode_manager.manager.RegisterNodeType(
    Alias, lambda x, *lst, **kw: Scons_alias_node_factory(SCons.Script.DefaultEnvironment().Alias, *lst, **kw))
