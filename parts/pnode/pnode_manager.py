
from __future__ import absolute_import, division, print_function

from builtins import map

import os

import SCons.Node
from SCons.Debug import logInstanceCreation

import parts.api as api
import parts.datacache as datacache
import parts.glb as glb
import parts.metatag as metatag
import parts.picklehelpers as picklehelpers
import parts.pnode.part_info as part_info  # needed for a type type
import parts.pnode.pnode as pnode


class _node_info(object):
    __slots__ = [
        '__csig',
        '__timestamp',
        '__id'
    ]

    def __init__(self, id, timestamp):
        if __debug__:
            logInstanceCreation(self)
        self.__csig = None
        self.__timestamp = timestamp
        self.__id = id

    @property
    def ID(self):
        return self.__id

    @property
    def TimeStamp(self):
        return self.__timestamp

    @property
    def CSig(self):
        if self.__csig is None:
            self.__csig = glb.pnodes.GetNodeIDMD5(self.__id)
        return self.__csig


class manager(object):
    """description of class"""

    _node_types = {}

    def __init__(self):
        if __debug__:
            logInstanceCreation(self)
        self.__known_pnodes = {}   # ID:node:parts.pnode
        self.__known_nodes = {}   # ID:SCons.Node.Node
        self.__aliases = {}  # ID:Alais node
        self.__store_all = False

        # cached states
        self.__cache = {}

        # map the events
        glb.engine.CacheDataEvent += self.Store
        glb.engine.PostProcessEvent += self._set_store_state
        glb.engine.PostProcessEvent += self.StoreAllPNodes

    def _set_store_state(self, mode):
        from ..loadlogic import all
        if mode == 'build' or mode == 'clean':
            self.__store_all = self._get_cache() is None
            if isinstance(glb.engine._part_manager.Loader, all.All):
                self.__store_all = True
                # clear out the cache
                datacache.StoreData("nodeinfo", {})

    def TotalNodes(self):
        return len(self.__known_nodes)

    def TotalPnodes(self):
        return len(self.__known_pnodes)

    def clear_node_states(self):
        for node in self.__known_nodes.values():
            node.clear_memoized_values()

    def isKnownNode(self, ID):
        return ID in self.__known_nodes

    def isKnownPNode(self, ID):
        return ID in self.__known_pnodes

    def isKnownAliasStored(self, ID):
        data = self._get_cache()
        if data:
            return ID in data.get('aliases', {})
        return False

    def isKnownNodeStored(self, ID):
        data = self._get_cache()
        if data:
            return ID in data.get('known_nodes', {})
        return False

    def isKnownPNodeStored(self, ID):
        data = self._get_cache()
        if data:
            return ID in data.get('known_pnodes', {})
        return False

    def GetNode(self, ID, create=None):
        try:
            return self.__known_nodes[ID]
        except KeyError:
            if self.isKnownNodeStored(ID):
                return self.LoadNodeStored(ID)
            elif create:
                return self.Create(create, ID)
        return None

    def GetPNode(self, ID, create=None):
        if self.isKnownPNode(ID):
            return self.__known_pnodes[ID]
        elif self.isKnownPNodeStored(ID):
            return self.LoadPNodeStored(ID)
        elif create:
            return self.Create(create, ID)
        return None

    def LoadNodeStored(self, ID):
        data = self._get_cache()
        if data:
            # get info on the type
            type = data['known_nodes'][ID]['type']
            # make "empty" node based on factory
            node = self.Create(type, ID=ID)
            return node
        return None

    def LoadPNodeStored(self, ID):
        data = self._get_cache()
        if data:
            # get info on the type
            type = data['known_pnodes'][ID]['type']
            # make "empty" node based on factory
            node = self.Create(type, ID=ID)
            return node
        return None

    def GetAliasStoredInfo(self, ID):
        data = self._get_cache()
        if data:
            try:
                return data['aliases'].get(ID)
            except KeyError:
                pass
        return None

    def GetStoredNodeInfo(self, node):
        return self.GetStoredNodeIDInfo(node.ID)

    def GetStoredNodeIDInfo(self, nodeID):
        data = self._get_cache()
        if data:
            try:
                return picklehelpers.loads(data['known_nodes'][nodeID]['pinfo'])
            except KeyError:
                return None
            except (TypeError, picklehelpers.UnpicklingError):
                # Old-style cache. Convert it into new one
                data = data['known_nodes'][nodeID]
                result = data['pinfo']
                data['pinfo'] = picklehelpers.dumps(result)
                return result
        return None

    def GetStoredPNodeInfo(self, node):
        return self.GetStoredPNodeIDInfo(node.ID)

    def GetStoredPNodeIDInfo(self, nodeID):
        data = self._get_cache()
        if data:
            try:
                return picklehelpers.loads(data['known_pnodes'][nodeID]['pinfo'])
            except KeyError:
                return None
            except (TypeError, picklehelpers.UnpicklingError):
                # Old-style cache. Convert it into new one
                data = data['known_pnodes'][nodeID]
                result = data['pinfo']
                data['pinfo'] = picklehelpers.dumps(result)
                return result
        return None

    def GetAllKnownStoredNodeIDs(self):
        data = self._get_cache()
        if data:
            try:
                ids = list(data['known_nodes'].keys())
                return ids
            except KeyError:
                pass
        return None

    # methods to allow us to track SCons.Nodes
    def AddNodeToKnown(self, node):
        self.__known_nodes[node.ID] = node

    def AddPNodeToKnown(self, node):
        self.__known_pnodes[node.ID] = node

    def AddAlias(self, node):
        self.__aliases[node.ID] = node

    def Aliases(self):
        return self.__aliases

    # factory methods
    @classmethod
    def RegisterNodeType(klass, node_type, create_func=None):
        if create_func is None:
            create_func = pnode.pnode_factory
        klass._node_types[node_type] = create_func

    def Create(self, ntype, *lst, **kw):
        return self._node_types[ntype](ntype, *lst, **kw)

    def _get_cache(self):
        stored_data = datacache.GetCache("nodeinfo")
        if not stored_data:
            stored_data = dict()
            datacache.StoreData("nodeinfo", stored_data)
        return stored_data

    def _set_cache(self, key, value):
        stored_data = self._get_cache()
        valuestostore = {} if stored_data is None else stored_data
        valuestostore[key] = value
        datacache.StoreData("nodeinfo", valuestostore)

    def store_value(self, node, _info, valuestostore):
        valuestostore[node.ID] = {
            'type': node.__class__,
            'pinfo': picklehelpers.dumps(_info)
        }

    def StoreAlias(self, node, valuestostore=None):
        stored_data = self._get_cache()

        if valuestostore is None:
            valuestostore = stored_data.get('aliases', {})

        binfo = node.get_binfo()
        # translate the node objects to a string value
        for a in ['bsources', 'bdepends', 'bimplicit']:
            try:
                val = getattr(binfo, a)
            except AttributeError:
                pass
            else:
                setattr(binfo, a, list(map(node_to_str, val)))
        valuestostore[node.ID] = binfo

        self._set_cache('aliases', valuestostore)

    def StoreNode(self, node):
        stored_data = self._get_cache()
        valuestostore = stored_data.get('known_nodes', {})

        # if we already have stored information, we want to make sure any incremental changes
        # that might need to be added and stored correctly
        if node.Stored:
            new_info = node.GenerateStoredInfo()
            newvalues = metatag.MetaTagValue(node, 'sections', ns='partinfo', default={})
            old_comp_data = node.Stored.Components
            for k1, v in new_info.Components.items():
                try:
                    old_comp_data[k1].update(v)
                except KeyError:
                    old_comp_data[k1] = v
            new_info.Components = old_comp_data
            self.store_value(node, new_info, valuestostore)
        else:
            # we have no stored information, so we assume the this build
            # had to load everything, and as such should have a complete
            # set to have stored
            self.store_value(node, node.GenerateStoredInfo(), valuestostore)

        self._set_cache('known_nodes', valuestostore)

    def StorePNode(self, pnode):
        data = {}
        stored_data = self._get_cache()
        valuestostore = stored_data.get('known_pnodes', {})

        # if this node is not valid anymore we want to remove it from known data
        if pnode._remove_cache:
            try:
                del valuestostore[pnode.ID]
            except KeyError:
                pass
        # This file was loaded, so we want to store information we have on it
        elif (pnode.LoadState == glb.load_file):
            sd = pnode.GenerateStoredInfo()
            self.store_value(pnode, sd, valuestostore)

        self._set_cache('known_pnodes', valuestostore)

    def StoreAllPNodes(self, build_mode):
        # this is mapped to the PostProcessEvent event to store all Pnode information we have
        for node in list(self.__known_pnodes.values()):
            if node.LoadState == glb.load_file:
                self.StorePNode(node)

    def Store(self, goodexit, build_mode='build'):
        # called at end of run to store and extra state that we can save,
        # but was not saved do to target, or build issues
        stored_data = self._get_cache()
        store_all = self.__store_all or stored_data is None
        if store_all:
            aliases_stored = 0
            for node in list(self.__aliases.values()):
                if not node.isVisited:
                    aliases_stored += 1
                    self.StoreAlias(node)

            nodes_stored = 0
            for node in list(self.__known_nodes.values()):
                if not node.isVisited or not self.GetStoredNodeIDInfo(node.ID):
                    nodes_stored += 1
                    self.StoreNode(node)
                    node.isVisited = True
                    if not isinstance(node, SCons.Node.FS.Base):
                        continue
                    srcnode = node.srcnode()
                    if node != srcnode and (not srcnode.isVisited or not self.GetStoredNodeIDInfo(srcnode.ID)):
                        nodes_stored += 1
                        self.StoreNode(srcnode)
                        srcnode.isVisited = True

            api.output.verbose_msg(['cache_save'], "Stored {0} aliases out of {1}".format(aliases_stored, len(self.__aliases)))
            api.output.verbose_msg(['cache_save'], "Stored {0} nodes out of {1}".format(nodes_stored, len(self.__known_nodes)))
        elif (not goodexit) or (build_mode == 'question'):
            datacache.ClearCache("nodeinfo")

    # this would mirror simular logic in the SCOns.Node classes
    # the goal here is to not load these Nodes as the memory hit
    # of these objects because of imple details is to high
    # which has a side effect of slowing down the build.
    def ClearNodeinfo(self, nodeid):
        self.__cache['NodeInfo'] = {}

    def Nodeinfo(self, nodeid):

        try:
            return self.__cache['NodeInfo'][nodeid]
        except KeyError:
            try:
                self.__cache['NodeInfo']
            except KeyError:
                self.__cache['NodeInfo'] = {}
            # we need to return a dict with two piece of information
            # 1) a timestamp given that it makes sence
            # 2) a csig value, or MD5 value of the context of the node

            # the trick is that object such as Aliases (and Values) are not yet defined
            # since the rule is that this logic only makes sense given node
            # changes on disk, values such as Alias are ignorable, since changes
            # that would modify what a given Alias is, is defined by the Context
            # defining files, such as a Part file, or a file that defines a builder
            # a different set of check looks to see if such a files changed, and set
            # the correct Part to a load state to make sure the taskmaster logic
            # can correct see what needs to be rebuilt if anything. Values are a little different
            # in that the can be built ( unlike Aliases at the moment), however that does
            # not effect anything for us, as the only risk is that the builder always
            # build a new value ( ie based on time or date) which we can't check for at the moment
            # and is the point of the force_load, AlwaysBuild logic for a Parts to make sure such items are always
            # such items are always loaded.
            # Because of this we only deal with node that are a type of are based on a
            # SCons.Node.FS.Base type.
            orgid = nodeid
            info = None
            if self.isNodeIDFileBased(nodeid):
                sinfo = self.GetStoredNodeIDInfo(nodeid)
                try:
                    st_info = os.lstat(os.path.abspath(os.path.normpath(nodeid)))
                except OSError:
                    st_info = None
                if st_info is None and sinfo.SrcNodeID:
                    nodeid = sinfo.SrcNodeID
                    try:
                        st_info = os.lstat(os.path.abspath(os.path.normpath(nodeid)))
                    except OSError:
                        st_info = None

                if st_info:
                    info = _node_info(nodeid, int(st_info.st_mtime))

            if info is None:
                info = _node_info(nodeid, 0)
            self.__cache['NodeInfo'][orgid] = info
        return info

    def GetNodeIDMD5(self, nodeid):
        tmp = self.GetNode(nodeid)
        if tmp:
            return tmp.get_csig()
        return 1
        # this is a bit ugly.. but is needed to avoid Node creation
        # to save on memory and time needed, until a SCons node refactor happens

        # if this is a file:
        # if self.GetNodeIDType(nodeid) == type(SCons.Node.FS.File):
        #    fname=os.path.abspath(nodeid)
        #    if os.path.exists(fname):
        #        return SCons.Util.MD5filesignature(fname,
        #            chunksize=SCons.Node.FS.File.md5_chunksize*1024)
        #    else:
        #        return SCons.Util.MD5signature('')
        # if this is a Value
        # elif self.GetNodeIDType(nodeid) == type(SCons.Node.Python.Value):

        # if this is a symlink based
        # elif self.GetNodeIDType(nodeid) == type(SCons.Node.FS.FileSymbolicLink):

        # else everything else is a csig of children values
        # else:

        # return SCons.Util.MD5signature(contents)

    def hasNodeRelationChanged(self, snode, ninfo):

        # This node may not be an File based value, so it may not have a time stamp
        # We cheat in that when we try to get the "timestamp" for node that don't have this
        # returning a 0 stored and 1 for current, this allows to force the MD5 check

        curr_info = self.Nodeinfo(snode)
        if ninfo.get('timestamp', 0) != curr_info.TimeStamp:
            # do MD5 check to see if it is really diffent
            if ninfo.get('csig', 0) != curr_info.CSig:
                api.output.verbose_msg(['node_check'], "{0} is out of date:\n current CSIG = {1}\n stored CSIG = {2}".format(
                    curr_info.ID, curr_info.CSig, ninfo.get('csig', 0)))
                return True
        return False

    def hasNodeChanged(self, nodeid):
        # checks stored information to find out if it a change has happened since the last time we tried to build
        # this given node ( or something needed to build items to build this node, etc...)

        # get stored info
        info = self.GetStoredNodeIDInfo(nodeid)
        if not info:
            api.output.verbose_msg(['node_check'], "{0} has no stored information".format(nodeid))
            return True

        # if this node is a file based. does it exist
        if issubclass(info.Type, SCons.Node.FS.Base):
            if issubclass(info.Type, SCons.Node.FS.FileSymbolicLink):
                exists = os.path.lexists
            else:
                exists = os.path.exists
            if not exists(nodeid):
                if info.SrcNodeID:
                    nodeid = info.SrcNodeID
                if not exists(nodeid):
                    api.output.verbose_msg(['node_check'], "{0} is out of date because it is not found on disk".format(nodeid))
                    return True

        # check to see if this has a AlwaysBuild() state set
        if info.AlwaysBuild:
            api.output.verbose_msg(['node_check'], "{0} is out of date because it was called with AlwaysBuild()".format(nodeid))
            return True

        src_data = info.SourceInfo

        # for each source check:
        for snode, ninfo in src_data.items():
            # if this node has changed
            if self.hasNodeRelationChanged(snode, ninfo):
                api.output.verbose_msg(
                    ['node_check'], "{0} is out of date because the state of source {1} is different from what is stored".format(nodeid, snode))
                return True

        return False

    def isNodeIDFileBased(self, nodeid):

        info = self.GetStoredNodeIDInfo(nodeid)
        if not info and self.isKnownNode(nodeid):
            return isinstance(self.GetNode(nodeid), SCons.Node.FS.Base)
        elif info:
            return issubclass(info.Type, SCons.Node.FS.Base)
        return False

    def GetChangedRootPartIDsSinceLastRun(self):
        ret = set([])
        stored_data = self._get_cache()
        if stored_data is None:
            return ret
        pnodes = stored_data.get('known_pnodes', {})
        for data in pnodes.values():
            try:
                pinfo = picklehelpers.loads(data['pinfo'])
            except (TypeError, picklehelpers.UnpicklingError):
                pinfo = data['pinfo']
                data['pinfo'] = picklehelpers.dumps(pinfo)
            if isinstance(pinfo, part_info.part_info):
                # if so test the Part file state
                tmp = pinfo.File
                if self.hasNodeRelationChanged(tmp['name'], tmp):
                    ret.add(pinfo.RootID)
        return ret




def node_to_str(node):
    if isinstance(node, SCons.Node.FS.File):
        t = node.path
        t = t.replace(os.sep, '/')
        return t
    elif isinstance(node, SCons.Node.FS.Dir):
        t = node.path
        t = t.replace(os.sep, '/')
        return t
    elif isinstance(node, SCons.Node.FS.Entry):
        t = node.path
        t = t.replace(os.sep, '/')
        return t
    elif SCons.Util.is_String(node):
        t = node
        t = t.replace(os.sep, '/')
        return t
    elif isinstance(node, SCons.Node.Python.Value):
        return node.value
    elif isinstance(node, SCons.Node.Alias.Alias):
        return node.name
    else:
        print("unknown type", node, type(node))
    return None

# vim: set et ts=4 sw=4 ai ft=python :
