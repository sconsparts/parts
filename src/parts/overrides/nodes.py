

import hashlib
import itertools
import os
import pprint
import stat
import sys
from builtins import zip

import parts.api as api
import parts.common as common
import parts.datacache as datacache
import parts.errors as errors
import parts.glb as glb
import parts.metatag as metatag
import parts.node_helpers as node_helpers
import SCons.Node
import SCons.Util
import SCons.SConsign
from parts.core import util
from parts.pnode import pnode_manager, scons_node_info
from SCons.Debug import logInstanceCreation


# Import symlinks to make sure it patches SCons.Node.FS and SCons.Environment before
# we refer it
from . import symlinks

SCons.Node.NodeList = SCons.Util.NodeList


Node = SCons.Node.Node
File = SCons.Node.FS.File
Dir = SCons.Node.FS.Dir
Entry = SCons.Node.FS.Entry
FileSymbolicLink = SCons.Node.FS.FileSymbolicLink
FSBase = SCons.Node.FS.Base
Value = SCons.Node.Python.Value
Alias = SCons.Node.Alias.Alias

_decider_map = SCons.Node._decider_map

# may need to have this called as a post read step to make sure custom deciders are wrapped correctly
for k, func in _decider_map.items():
    def override_decider(dependency, target, prev_ni, repo_node=None):
        # we cannot do this a better way in SCons yet.. this allows us to make sure the statefile
        # are built when ever a timestamp change happens. This check has to be a target file in the
        # .part.cache ( which makes it a state file of some type)
        if target.ID.startswith(".parts.cache"):
            return _changed_timestamp_match(dependency, target, prev_ni, repo_node)
        # else call default logic whatever that may be
        return func(dependency, target, prev_ni, repo_node)
    _decider_map[k] = override_decider


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


def _repr_(self):
    return f"<{self.__class__.__name__} object ID:{self.ID} at {id(self)}>"

Node.__repr__ = _repr_

class wrapper:

    def __init__(self, binfo, ninfo=None):
        if __debug__:
            logInstanceCreation(self)
        self.binfo = binfo
        self.ninfo = ninfo


class fake_ninfo:
    __slots__ = ['timestamp', 'csig']

    def __init__(self, timestamp, csig):
        if __debug__:
            logInstanceCreation(self)
        self.timestamp = timestamp
        self.csig = csig


Node.make_ninfo_from_dict = lambda self, dict: fake_ninfo(dict.get('timestamp', 0), dict.get('csig', 0))


def action_changed(self, binfo=None, indent=0):
    '''
    given node as builder .. is the action sig different
    '''
    # if the node is build or visited it cannot be viewed as changed anymore
    if self.isBuilt or self.isVisited:

        return False

    if self.has_builder():  # check to be safe that this has a builder
        # then we need to have stored information else this is viewed as changed

        if not binfo:
            if not self.has_stored_info():
                return True
            info = self.get_stored_info()
            binfo = info.binfo

        contents = self.get_executor().get_contents()
        newsig = SCons.Util.MD5signature(contents)
        oldsig = binfo.bactsig
        if oldsig != newsig:
            api.output.verbose_msgf(["node-changed"], "{indent}Action changed for {node} changed! oldsig={oldsig} newsig={newsig}",
                                    node=self.ID, oldsig=oldsig, newsig=newsig, indent=" "*indent)
            return True

    return False


SCons.Node.Node.action_changed = action_changed

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


def wrap_visited(klass):
    _visited = klass.visited

    def set_visited(self, *lst, **kw):
        # call scons function
        ret = _visited(self, *lst, **kw)
        self.attributes._isVisited = True
        return ret
    klass.visited = set_visited


# is this a child of this node
wrap_visited(SCons.Node.Node)
wrap_visited(SCons.Node.FS.File)


def is_child(self, node):
    # we don't call the children() api as much as we would like to
    # as this cached data and calls the scanner. We just want this
    # to be called on the known nodes
    children = (self.sources if self.sources else []) + \
        (self.depends if self.depends else []) + \
        (self.implicit if self.implicit else [])

    return True if node in children else False


SCons.Node.Node.is_child = is_child


def is_side_effect(self):
    '''
    silly function to make code more readable
    '''
    return self.side_effect


SCons.Node.Node.is_side_effect = is_side_effect


def is_buildable(self):
    ''' 
    return True if the node has a builder or is a SideEffect of a different builder
    If this is a Directory node we want to return False if the builder is the builtin
    default SCons.Node.FS.MkdirBuilder as this case does not store information in the DB
    '''
    return (self.has_builder() or self.is_side_effect()) and not self.builder is SCons.Node.FS.MkdirBuilder


SCons.Node.Node.is_buildable = is_buildable


def get_timestamp_dir(self):
    """
    Get the timestamp of a directory
    At the moment the logic is to test all the children that exist.
    and get the latest timestamp value. This only goes down one level
    and differs from the system logic is that child directories timestamp 
    changes are seen. This might change going forward. However this means
    that the newest node in the subtree should be seen
    """
    stamp = 0
    for child in self.children():
        ts = child.get_timestamp()
        if child.exists() and ts > stamp:
            stamp = child.get_timestamp()
    if not stamp:
        stamp = self.getmtime()
    return stamp


SCons.Node.FS.Dir.get_timestamp = get_timestamp_dir


def update_binfo_dir(self):
    ''' 
    This is generally only a function needed for Directory nodes
    as only directory nodes can be built and have implicit items added
    after the fact that could cause false rebuilds on the second pass
    of a build.
    Here we want to re-store the information after we clear the binfo
    '''
    if self.isVisited and self.builder is not SCons.Node.FS.MkdirBuilder:
        try:
            # delete the binfo ( it might not exist )
            del self.binfo
        except AttributeError:
            pass
        # get the children again.. given this should not happen a lot if at all
        # regenerating this should not be a big deal
        self.scan()
        # restore the item in the DB
        SCons.Node.store_info_map[self.store_info](self)


SCons.Node.FS.Dir.update_binfo = update_binfo_dir


def builder_set(self, builder):
    SCons.Node.Node.builder_set(self, builder)
    if self.builder is not SCons.Node.FS.MkdirBuilder:
        self.changed_since_last_build = 5


SCons.Node.FS.Dir.builder_set = builder_set


def visited_dir(self):
    if self.exists() and self.executor is not None:
        self.get_build_env().get_CacheDir().push_if_forced(self)

    ninfo = self.get_ninfo()

    ninfo.timestamp = self.get_timestamp()
    ninfo.csig = self.get_csig()
    # print(self.ID,"%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    self.isVisited = True
    # for a directory it always has a builder
    # what we care about is if the builder if the default
    # builtin MkdirBuilder one. If it is the default we don't want to store
    # any extra information.
    if self.builder is SCons.Node.FS.MkdirBuilder:
        # default logic is scons is not store information about the directories
        #self.store_info = 0
        pass
    else:
        # there is a bug in SCons at the moment in which a target scanner would not have
        # executed yet for this node ( or not applied as expected). This would cause the
        # implicited depends to be missing causing a false rebuild on the next pass.
        # this forces everything to be clean up before we try to store the binfo
        self.implicit = []
        self.implicit_set = set([])

        executor = self.get_executor()
        executor.scan_sources(self.builder.source_scanner)
        # If there's a target scanner, have the executor scan the target
        # node itself and associated targets that might be built.
        scanner = self.get_target_scanner()
        if scanner:
            executor.scan_targets(scanner)

    # this does the store of information in the DB file
    # the store logic is to get the stored info
    # and then merge this with the current binfo
    # this will be saved at some point by scons on disk
    SCons.Node.store_info_map[self.store_info](self)


SCons.Node.FS.Dir.visited = visited_dir


def node_file(self, nodestr):
    '''
    This is a factory function that creates a node of the correct type
    based on the string
    '''

    if not os.path.exists(nodestr):
        return self.fs.Entry(nodestr)
    elif os.path.islink(nodestr):
        return self.fs.FileSymbolicLink(nodestr)
    return self.fs.File(nodestr)


SCons.Node.FS.FileNodeInfo.node = node_file


def node_value(self, nodestr):
    '''
    This is a factory function that creates a node of the correct type
    based on the string
    '''
    return Value(nodestr)


SCons.Node.Python.ValueNodeInfo.node = node_value


def node_alias(self, nodestr):
    '''
    This is a factory function that creates a node of the correct type
    based on the string
    '''
    return Alias(nodestr)


SCons.Node.Alias.AliasNodeInfo.node = node_value


class DirNodeInfo(SCons.Node.NodeInfoBase):
    __slots__ = ('csig', 'timestamp')  # , 'size')
    # This should get reset by the FS initialization.
    current_version_id = 2

    fs = None

    def str_to_node(self, s):
        top = self.fs.Top
        root = top.root
        if SCons.Node.FS.do_splitdrive:
            drive, s = SCons.Node.FS._my_splitdrive(s)
            if drive:
                root = self.fs.get_root(drive)
        if not os.path.isabs(s):
            s = top.get_labspath() + '/' + s
        return root._lookup_abs(s, Entry)

    def node(self, nodestr):
        '''
        This is a factory function that creates a node of the correct type
        based on the string
        '''
        return self.fs.Dir(nodestr)


DirNodeInfo.fs = SCons.Node.FS.DirNodeInfo.fs
SCons.Node.FS.DirNodeInfo = DirNodeInfo


def convert_from_sconsignFbinfo(self, dir, name):
    """
    Converts the "string" version of the node back into nodes based 
    on the type of info we stored in the sigs version
    """
    try:
        self.bsources = [sig.node(val) for val, sig in zip(self.bsources, self.bsourcesigs)]
        self.bdepends = [sig.node(val) for val, sig in zip(self.bdepends, self.bdependsigs)]
        self.bimplicit = [sig.node(val) for val, sig in zip(self.bimplicit, self.bimplicitsigs)]
    except:
        pass


SCons.Node.FS.FileBuildInfo.convert_from_sconsign = convert_from_sconsignFbinfo


class DirBuildInfo(SCons.Node.BuildInfoBase):
    __slots__ = ('dependency_map')
    current_version_id = 2

    def __setattr__(self, key, value):

        # If any attributes are changed in FileBuildInfo, we need to
        # invalidate the cached map of file name to content signature
        # heald in dependency_map. Currently only used with
        # MD5-timestamp decider
        if key != 'dependency_map' and hasattr(self, 'dependency_map'):
            del self.dependency_map

        return super(DirBuildInfo, self).__setattr__(key, value)

    def convert_to_sconsign(self):
        """
        Converts this FileBuildInfo object for writing to a .sconsign file

        This replaces each Node in our various dependency lists with its
        usual string representation: relative to the top-level SConstruct
        directory, or an absolute path if it's outside.
        """
        if SCons.Node.FS.os_sep_is_slash:
            node_to_str = str
        else:
            def node_to_str(n):
                try:
                    s = n.get_internal_path()
                except AttributeError:
                    s = str(n)
                else:
                    s = s.replace(SCons.Node.FS.OS_SEP, '/')
                return s
        try:
            self.bsources = [node_to_str(val) for val in self.bsources]
        except AttributeError:
            self.bsources = []
        try:
            self.bdepends = [node_to_str(val) for val in self.bdepends]
        except AttributeError:
            self.bdepends = []
        try:
            self.bimplicit = [node_to_str(val) for val in self.bimplicit]
        except AttributeError:
            self.bimplicit = []

    def convert_from_sconsign(self, dir, name):
        """
        Converts the "string" version of the node back into nodes based 
        on the type of info we stored in the sigs version
        """
        self.bsources = [sig.node(val) for val, sig in zip(self.bsources, self.bsourcesigs)]
        self.bdepends = [sig.node(val) for val, sig in zip(self.bdepends, self.bdependsigs)]
        self.bimplicit = [sig.node(val) for val, sig in zip(self.bimplicit, self.bimplicitsigs)]

    def prepare_dependencies(self):
        """
        Prepares a FileBuildInfo object for explaining what changed

        The bsources, bdepends and bimplicit lists have all been
        stored on disk as paths relative to the top-level SConstruct
        directory.  Convert the strings to actual Nodes (for use by the
        --debug=explain code and --implicit-cache).
        """
        attrs = [
            ('bsources', 'bsourcesigs'),
            ('bdepends', 'bdependsigs'),
            ('bimplicit', 'bimplicitsigs'),
        ]
        for (nattr, sattr) in attrs:
            try:
                strings = getattr(self, nattr)
                nodeinfos = getattr(self, sattr)
            except AttributeError:
                continue
            if strings is None or nodeinfos is None:
                continue
            nodes = []
            for s, ni in zip(strings, nodeinfos):
                if not isinstance(s, SCons.Node.Node):
                    s = ni.str_to_node(s)
                nodes.append(s)
            setattr(self, nattr, nodes)

    def format(self, names=0):
        result = []
        bkids = self.bsources + self.bdepends + self.bimplicit
        bkidsigs = self.bsourcesigs + self.bdependsigs + self.bimplicitsigs
        for bkid, bkidsig in zip(bkids, bkidsigs):
            result.append(str(bkid) + ': ' +
                          ' '.join(bkidsig.format(names=names)))
        if not hasattr(self, 'bact'):
            self.bact = "none"
        result.append('%s [%s]' % (self.bactsig, self.bact))
        return '\n'.join(result)


SCons.Node.FS.DirBuildInfo = DirBuildInfo

SCons.Node.FS.Dir.NodeInfo = DirNodeInfo
SCons.Node.FS.Dir.BuildInfo = DirBuildInfo

# update checks for some non file nodes so they can be used correctly as
# targets in a builder


def changed_content(self, target, prev_ni, repo_node=None):
    cur_csig = self.get_csig()
    try:
        return cur_csig != prev_ni.csig
    except AttributeError:
        return True


SCons.Node.FS.Dir.changed_content = changed_content
SCons.Node.Python.Value.changed_content = changed_content


def changed_timestamp_then_content(self, target, prev_ni, node=None):
    # for Values at the moment timestamp has no real meaning
    # for Dir nodes it can be misleading in the case of directories so we just check for
    # content changes
    # might change in the future
    return self.changed_content(target, prev_ni, node)


SCons.Node.FS.Dir.changed_timestamp_then_content = changed_content
SCons.Node.Python.Value.changed_timestamp_then_content = changed_content


def is_up_to_date_dir(self):
    """
    If this is the default MkdirBuilder
    it is up-to-date if the children exists
    else we want to check binfo 
    """
    # check that we exist
    if self.builder is not SCons.Node.FS.MkdirBuilder and not self.exists():
        return False
    if self.builder is SCons.Node.FS.MkdirBuilder:
        # check the child node is up_to_date
        up_to_date = SCons.Node.up_to_date
        for kid in self.children():
            if kid.get_state() > up_to_date:
                return False
    else:
        result = node_helpers.has_changed(self)

        # if the result at this point is still not changed
        # check action signiture
        if not result:
            result = action_changed(self)
        return not result
    return True


# do the overide
SCons.Node.FS.Dir.is_up_to_date = is_up_to_date_dir

###############################################
# Allow directory nodes to work in a builder


def get_found_includes_dir(self, env, scanner, path):
    if not scanner:
        return []
    if self.builder is SCons.Node.FS.MkdirBuilder and not self.isVisited:
        # #### notes from original function on "default" behavior we want to
        # #### keep if this the default scanner. We only change it to not
        # #### clear() when the node is visited

        # Clear cached info for this Dir.  If we already visited this
        # directory on our walk down the tree (because we didn't know at
        # that point it was being used as the source for another Node)
        # then we may have calculated build signature before realizing
        # we had to scan the disk.  Now that we have to, though, we need
        # to invalidate the old calculated signature so that any node
        # dependent on our directory structure gets one that includes
        # info about everything on disk.
        self.clear()

    # elif self.isVisited:
        # if this is a custom builder and
        # if this is build already just return what we know
        # return self.implicit
    # call scanner to get values
    return scanner(self, env, path)


SCons.Node.FS.Dir.get_found_includes = get_found_includes_dir


def get_env_scanner(self, env, kw={}):
    if self.builder is not SCons.Node.FS.MkdirBuilder:
        return None  # self.builder.target_scanner
    return SCons.Defaults.DirEntryScanner


SCons.Node.FS.Dir.get_env_scanner = get_env_scanner


def get_target_scanner(self):
    if self.builder is not SCons.Node.FS.MkdirBuilder:
        return self.builder.target_scanner
    return SCons.Defaults.DirEntryScanner


SCons.Node.FS.Dir.get_target_scanner = get_target_scanner

############################################
# deal with stored information


def get_stored_info_dir(self):
    try:
        return self._memo['get_stored_info']
    except KeyError:
        pass

    try:
        # try to get stored data
        sconsign_entry = self.dir.sconsign().get_entry(self.name)
    except (KeyError, EnvironmentError):
        # it failed so create default
        sconsign_entry = SCons.SConsign.SConsignEntry()
        sconsign_entry.binfo = self.new_binfo()
        sconsign_entry.ninfo = self.new_ninfo()

    self._memo['get_stored_info'] = sconsign_entry

    return sconsign_entry


# do the overide
SCons.Node.FS.Dir.get_stored_info = get_stored_info_dir


def has_stored_info_fs(self):
    '''
    We want to know if we have build info or not
    '''
    try:
        self.dir.sconsign().get_entry(self.name)
        return True
    except (KeyError, EnvironmentError):
        return False


SCons.Node.FS.Base.has_stored_info = has_stored_info_fs

# add a isBuilt property as read only.
# will be set via an overide to the built() function (ie set after SCons defalut logic is called)


def _get_isBuilt(self):
    try:
        return self.attributes._isBuilt
    except AttributeError:
        return False


def wrap_built(klass):
    _built = klass.built

    def set_built(self, *lst, **kw):
        # call scons function
        # built does not return anything at the moment
        # we do this to be safe in case it changed
        ret = _built(self, *lst, **kw)
        self.attributes._isBuilt = True
        return ret
    klass.built = set_built


# the node is needed
wrap_built(SCons.Node.Node)

SCons.Node.Node.isBuilt = property(_get_isBuilt)


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


def def_FS_Dir___init__(klass):
    orig = klass.__init__

    def __init__(self, name, directory, fs):
        orig(self, name, directory, fs)
        self.changed_since_last_build = 4
    klass.__init__ = __init__


def_FS_Dir___init__(SCons.Node.FS.Dir)


def _my_init(self, *lst, **kw):
    self.orig_init(*lst, **kw)
    # may not be the best way.. but works for the moment
    glb.pnodes.AddNodeToKnown(self)


SCons.Node.Python.Value.orig_init = SCons.Node.Python.Value.__init__
SCons.Node.Python.Value.__init__ = _my_init

# to allow directories to work correctly as build target to a builder


def _morph_dir(self):
    self.orig_morph()
    if self.builder is not SCons.Node.FS.MkdirBuilder:
        self.changed_since_last_build = 5


SCons.Node.FS.Dir.orig_morph = SCons.Node.FS.Dir._morph
SCons.Node.FS.Dir._morph = _morph_dir


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

# overide allows us to set Decider on a node without having to pass in a function


def _changed_content(dependency, target, prev_ni, repo_node=None):
    return dependency.changed_content(target, prev_ni, repo_node)


def _changed_timestamp_then_content(dependency, target, prev_ni, repo_node=None):
    try:
        return dependency.changed_timestamp_then_content(target, prev_ni, repo_node)
    except AttributeError:
        return dependency.changed_content(target, prev_ni, repo_node)


def _changed_timestamp_newer(dependency, target, prev_ni, repo_node=None):
    try:
        return dependency.changed_timestamp_newer(target, prev_ni, repo_node)
    except AttributeError:
        return dependency.changed_content(target, prev_ni, repo_node)


def _changed_timestamp_match(dependency, target, prev_ni, repo_node=None):
    try:
        return dependency.changed_timestamp_match(target, prev_ni, repo_node)
    except AttributeError:
        return dependency.changed_content(target, prev_ni, repo_node)


def _part_decider(self, function):
    # check to see if this is a string
    # if so this allow us to decider function that are defined as part of the
    # environment object. call the same logic as getting environments here is
    # expensive when we don't need it

    if function in ('MD5', 'content'):
        function = _changed_content
    elif function == 'MD5-timestamp':
        function = _changed_timestamp_then_content
    elif function in ('timestamp-newer', 'make'):
        function = _changed_timestamp_newer
    elif function == 'timestamp-match':
        function = _changed_timestamp_match
    elif not callable(function):
        # if this callable? if not error out now.
        raise SCons.Errors.UserError("Unknown Decider value %s" % repr(function))

    # call default node logic that expects a function
    return self.orig_decider(function)


SCons.Node.Node.orig_decider = SCons.Node.Node.Decider
SCons.Node.Node.Decider = _part_decider


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
    for partid, sections in info.Components.items():
        info.Components[partid] = set([sec.ID for sec in sections])

    info.AlwaysBuild = bool(self.always_build)
    if isinstance(self, FSBase):
        try:
            if self.ID != self.srcnode().ID and not self.exists() and self.srcnode().exists():
                info.SrcNodeID = self.srcnode().ID
        except Exception:
            pass

    if self.has_builder() or self.side_effect:
        binfo = self.get_binfo()
        nodes = list(zip(getattr(binfo, 'bsources', []) + getattr(binfo, 'bdepends', []) + getattr(binfo, 'bimplicit', []),
                         binfo.bsourcesigs + binfo.bdependsigs + binfo.bimplicitsigs))
    else:
        nodes = []

    new_binfo = {}

    for node, ninfo in nodes:
        # some time the node info is a string not a Node object
        try:
            key = node.ID
        except Exception:
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
                (entry, None) for name, entry in node.entries.items()
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
