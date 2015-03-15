import sys
import os
import re
import cPickle
import base64
import cStringIO
import collections
import copy

import scons_setup
import parts_setup

scons_setup.setupDefault()
parts_setup.setupDefault()
import parts.pickle_helpers as pickle_helpers
import parts.datacache as datacache
import parts.glb as glb
import parts.pnode.section_info as parts_pnode_section_info
import parts.pnode.part_info as parts_pnode_part_info
import parts.pnode.scons_node_info as parts_pnode_scons_node_info
import parts.target_type as parts_target_type

def _preWorkWithCache(cacheFilePath):
    (cacheRootDir, cacheDirName, cacheKey, cacheFileName) = split(cacheFilePath)

    # Workaround to let Parts find cache file even if this script is not called
    # from directory where '.parts.cache' directory resides
    load_cache_data_orig = datacache.load_cache_data
    def load_cache_data_wrapper(datafile):
        datafileCopy = copy.deepcopy(datafile)
        if not os.path.exists(datafile) and datafile.startswith(cacheDirName):
            datafileCopy = os.path.join(cacheRootDir, datafile)
        assert(os.path.exists(datafileCopy))
        return load_cache_data_orig(datafileCopy)
    datacache.load_cache_data = load_cache_data_wrapper

    try:
        cacheKeyOrig = glb.engine._cache_key
    except:
        cacheKeyOrig = None
    glb.engine._cache_key = cacheKey

    return (load_cache_data_orig, cacheKeyOrig)

def _postWorkWithCache(origData):
    glb.engine._cache_key = origData[1]
    datacache.load_cache_data = origData[0]

class CacheFilenames:
    DIR_NAME_CACHE = '.parts.cache'
    FILE_NODEINFO = 'nodeinfo'
    FILE_VCS = 'vcs'
    FILE_GLOBAL_DATA = 'global_data'
    FILE_PART_MAP = 'part_map'
    EXT_CACHE = '.cache'

class NodeinfoKeys:
    KNOWN_PNODES = 'known_pnodes'
    KNOWN_NODES = 'known_nodes'
    ALIASES = 'aliases'

class PartMapKeys:
    HAS_CLASSIC = 'hasClassic'
    KNOWN_PARTS = 'known_parts'
    NAME_TO_ALIAS = 'name_to_alias'

class VcsKeys:
    COMPLETED = 'completed'
    TYPE = 'type'
    SERVER = 'server'

class NodeinfoParser():
    def __init__(self, nodeinfoPath, reportProgress = None):
        """
        "nodeinfoPath" - path to nodeinfo.cache file
        """
        percentsUnpickle = 9
        percentsParsePnodes = 10
        percentsNodesNoDepends = 90
        percentsNodesDepends = 100

        if reportProgress:
            reportProgress(0)

        self.__nodeinfoPath = None

        # Structure is: {partAlias: partName}
        self.__aliasToName = {}

        # Structure is: {partAlias: [sectionName, ...] }
        self.__aliasToSections = collections.defaultdict(set)

        # Structure is {partAlias: (vcsType, vcsServer) }
        self.__aliasToVcsInfo = {}

        # Structure is {partAlias: srcPath }
        self.__aliasToSrcPath = {}

        # Structure is: { partAlias: [ (nodeId, nodeDict, nodeObj) ] }
        self.__aliasToNodes = collections.defaultdict(list)

        if not os.path.isfile(nodeinfoPath):
            raise ValueError('Not a valid filepath: %s' % str(nodeinfoPath))

        self.__nodeinfoPath = nodeinfoPath

        def reportProgressUnpickle(percentsDone):
            if reportProgress:
                progressMade = int(percentsUnpickle * float(percentsDone) / 100)
                reportProgress(progressMade)
        storedData = unpickle(nodeinfoPath, reportProgressUnpickle)
        assert(isinstance(storedData, dict))

        if reportProgress:
            reportProgress(percentsUnpickle)

        if NodeinfoKeys.KNOWN_PNODES not in storedData:
            raise Exception('File "%s" does not contain section "%s"' % (nodeinfoPath,
                NodeinfoKeys.KNOWN_PNODES))

        (cacheRootDir, cacheDirName, cacheKey, cacheName) = split(self.__nodeinfoPath)
        cacheVcsDir = os.path.join(cacheRootDir, cacheDirName, 'vcs')

        origData = _preWorkWithCache(self.__nodeinfoPath)

        pnodes = storedData[NodeinfoKeys.KNOWN_PNODES]
        assert(isinstance(pnodes, dict))
        for k, v in pnodes.iteritems():
            if isinstance(v, parts_pnode_section_info.section_info):
                continue
            elif isinstance(v, parts_pnode_part_info.part_info):
                self.__aliasToName[v.ID] = v.Name
                self.__aliasToSections[v.ID].update(set([v.SectionIDs[secName] for secName in v.SectionIDs]))
                self.__aliasToSrcPath[v.ID] = v.SrcPath

                partVcsCacheFile = None
                if v.VcsCacheFilename:
                    # 'vcs_cache_filename' should be filled and we should get valid path to cache file
                    partVcsCacheFile = os.path.join(cacheVcsDir, v.VcsCacheFilename) + '.cache'
                # Code below contains various workarounds for the case when 'vcs_cache_filename' is empty
                # for some reason.
                if not partVcsCacheFile or not os.path.exists(partVcsCacheFile) or not os.path.isfile(partVcsCacheFile):
                    partVcsCacheFile = os.path.join(cacheVcsDir, v.ID) + '.cache'
                if not os.path.exists(partVcsCacheFile) or not os.path.isfile(partVcsCacheFile):
                    # If part alias has platform suffix then vcs cache file does not have it
                    # because VcsReuse is used.
                    # TODO: Store info about VcsReuse in cache for specific part (just store name of vcs cache file?)
                    for suffix in ['x86', 'x86_64']:
                        if v.ID.endswith(suffix):
                            partVcsCacheFile = os.path.join(cacheVcsDir, v.ID[:-len(suffix)]) + '.cache'
                            break
                if not os.path.exists(partVcsCacheFile) or not os.path.isfile(partVcsCacheFile):
                    vcsIdx = v.SrcPath.find('vcs')
                    assert(vcsIdx != -1)
                    srcPath = v.SrcPath[vcsIdx:]
                    srcPathParts = srcPath.split(os.path.sep)
                    assert(srcPathParts[0] == 'vcs')
                    if len(srcPathParts) > 1:
                        partVcsCacheFile = os.path.join(cacheVcsDir, srcPathParts[1]) + '.cache'
                if os.path.exists(partVcsCacheFile) and os.path.isfile(partVcsCacheFile):
                    storedDataVcs = unpickle(partVcsCacheFile)
                    assert(isinstance(storedDataVcs, dict))
                    self.__aliasToVcsInfo[v.ID] = (storedDataVcs.get(VcsKeys.TYPE),
                        storedDataVcs.get(VcsKeys.SERVER))
            else:
                raise Exception('Unknown type of pnode: {0}'.format(type(v)))

        if reportProgress:
            reportProgress(percentsParsePnodes)

        if NodeinfoKeys.KNOWN_NODES not in storedData:
            raise Exception('File "%s" does not contain section "%s"' % (nodeinfoPath,
                NodeinfoKeys.KNOWN_NODES))

        # Structure is {partAlias: set(nodePath0, nodePath1, ...)}
        addedNodes = collections.defaultdict(set)

        def addNode(nodePath, nodeInfo, partAlias, addedNodes, addDepends):
            if nodePath in addedNodes[partAlias]:
                assert(addDepends)
                return

            try:
                nodeObj = glb.pnodes.GetNode(nodePath)
            except Exception, err:
                nodeObj = None

            if not nodeObj:
                sys.stderr.write('WARNING: Unable to create node "%s"' % nodePath)

            storedInfo = nodeObj.get_stored_info() if nodeObj else None
            nodeDict = { 'nodeInfo': nodeInfo, 'nodeInfoSrcNode': nodeInfo.SrcNode(None), 'partAlias': partAlias }
            depends = storedInfo.binfo.bdepends if (storedInfo is not None and \
                hasattr(storedInfo.binfo, 'bdepends')) else []
            if depends:
                nodeDict['depends'] = depends
            self.__aliasToNodes[partAlias].append((nodePath, nodeDict, nodeObj))
            addedNodes[partAlias].add(nodePath)
            if depends and addDepends:
                nodeInfoForDepends = None
                if nodeInfo:
                    nodeInfoForDepends = parts_pnode_scons_node_info.scons_node_info()
                    nodeInfoForDepends.type = nodeInfo.Type
                    nodeInfoForDepends.components = nodeInfo.Components
                for nodePathCurr in depends:
                    addNode(nodePathCurr, nodeInfoForDepends, partAlias, addedNodes, addDepends)

        nodes = storedData[NodeinfoKeys.KNOWN_NODES]
        assert(isinstance(nodes, dict))
        nodePaths = nodes.keys()
        progressReported = percentsParsePnodes
        for i in range(len(nodePaths)):
            nodePath = nodePaths[i]
            nodeInfo = nodes[nodePath]
            components = nodeInfo.Components
            assert(isinstance(components, dict))
            for partAlias, sectionSet in components.iteritems():
                assert(nodePath not in addedNodes[partAlias])
                addNode(nodePath, nodeInfo, partAlias, addedNodes, False)

            if reportProgress:
                progressMade = int(percentsParsePnodes + (percentsNodesNoDepends - \
                    percentsParsePnodes) * float(i) / len(nodePaths))
                if progressMade > progressReported:
                    reportProgress(progressMade)
                    progressReported = progressMade

        partAliases = self.__aliasToNodes.keys()
        for i in range(len(partAliases)):
            partAlias = partAliases[i]
            for nodePath, nodeDict, nodeObj in self.__aliasToNodes[partAlias]:
                depends = nodeDict.get('depends')
                if depends:
                    nodeInfoForDepends = None
                    if 'nodeInfo' in nodeDict:
                        nodeInfoForDepends = parts_pnode_scons_node_info.scons_node_info()
                        nodeInfoForDepends.type = nodeDict['nodeInfo'].type
                        nodeInfoForDepends.components = nodeDict['nodeInfo'].components
                    for nodePathCurr in depends:
                        addNode(nodePathCurr, nodeInfoForDepends, partAlias, addedNodes, True)

            if reportProgress:
                progressMade = int(percentsNodesNoDepends + (percentsNodesDepends - \
                    percentsNodesNoDepends) * float(i) / len(partAliases))
                if progressMade > progressReported:
                    reportProgress(progressMade)
                    progressReported = progressMade

        if reportProgress:
            reportProgress(100)

        _postWorkWithCache(origData)

    def getAliases(self):
        return self.__aliasToSections.keys()

    def getPartName(self, partAlias):
        return self.__aliasToName.get(partAlias)

    def getSectionNames(self, partAlias):
        return self.__aliasToSections.get(partAlias, set())

    def getVcsInfo(self, partAlias):
        return self.__aliasToVcsInfo.get(partAlias, (None, None))

    def getSrcPath(self, partAlias):
        return self.__aliasToSrcPath.get(partAlias)

    def getNodes(self, partAlias, section = 'build', nodeType = None, rootDir = None,
            extensions = [], masks = [], existingOnly = True):
        """
        Return list of tuples (nodeId, nodeDict, nodeObj) for particular part.
        Here "nodeDict" is a dictionary containing frequently used information for node.
        Currently the following key-value pairs can be present in it:
         * 'nodeInfo': instance of parts.pnode.scons_node_info.scons_node_info.
         * 'depends': list of strings representing dependencies for node. For Dir and File node types only.
        "nodeObj" is an instance of node and "nodeId" is:
         * path to node for SCons.Node.FS.File and SCons.Node.FS.Dir
         * alias for SCons.Node.Alias.Alias
         * value for SCons.Node.Python.Value

        "partAlias" - alias of component to get nodes for
        "section" - name of section. Default is "build". Can be None meaning that nodes
                    for any section should be returned.
        "nodeType" - type of node. Default is None meaning that nodes
                     of any types should be returned.
        "rootDir" - directory which node paths are relative to. Applicable only if "nodeType" is File or Dir.
                    Default is None meaning that it is a directory where .parts_pache recides.
        "extensions" - extensions of nodes to be included. Applicable only if "nodeType" is File. Default
                       is [] meaning that nodes with all extensions should be returned
        "masks" - regexp patterns which returned nodes should match.  Default is [].
        "existingOnly" - specifies whether only nodes existing on disk should be returned. Default is True.
        """
        if partAlias not in self.__aliasToNodes:
            return []

        (cacheRootDir, cacheDirName, cacheKey, cacheName) = split(self.__nodeinfoPath)
        nodeRootDir = cacheRootDir if rootDir is None else rootDir

        maskRexes = [re.compile(i) for i in masks]

        import SCons.Node

        retVal = []
        for nodeId, nodeDict, nodeObj in self.__aliasToNodes[partAlias]:
            nodeInfo = nodeDict['nodeInfo']
            sectionSet = set(nodeInfo.Components[partAlias]) # set of section IDs
            currNodeType = nodeInfo.Type
            srcNode = str(nodeDict['nodeInfoSrcNode'])
            if section is not None and (section + '::' + partAlias) not in sectionSet:
                continue
            if nodeType is not None and nodeType != currNodeType:
                continue

            if currNodeType == SCons.Node.Python.Value or currNodeType == SCons.Node.Alias.Alias:
                # "extensions", "masks" and "existingOnly" filtering options are not applied,
                # need to add this node to retVal
                retVal.append((nodeId.replace('/', os.path.sep), nodeDict, nodeObj))
                continue

            assert(currNodeType == SCons.Node.FS.File or currNodeType == SCons.Node.FS.Dir)
            nodePaths = [nodeId]
            if srcNode:
                nodePaths.append(srcNode)

            for nodePathCurr in nodePaths:
                fullNodePath = nodePathCurr
                if not os.path.isabs(fullNodePath):
                    fullNodePath = os.path.join(nodeRootDir, nodePathCurr)

                if existingOnly and not os.path.exists(fullNodePath):
                    continue

                if extensions and currNodeType == SCons.Node.FS.File and \
                        os.path.splitext(nodePathCurr)[1] not in extensions:
                    continue

                if maskRexes and not any([i.search(nodePathCurr) for i in maskRexes]):
                    continue

                retVal.append((nodePathCurr.replace('/', os.path.sep),
                    nodeDict if nodePathCurr == nodeId else {'partAlias': partAlias},
                    nodeObj if nodePathCurr == nodeId else None))

        return retVal

# Returns tuple (cacheRootDir, cacheDirName, cacheKey, cacheFileName)
# E.g. if cacheFilePath is "zip_package1/.parts.cache/a3e124cd59bd929fed1f43ec55421e66/nodeinfo.cache"
# then it will return ("zip_package1", ".parts.cache", "a3e124cd59bd929fed1f43ec55421e66", "nodeinfo")
def split(cacheFilePath):
    (cacheFileDir, cacheFile) = os.path.split(os.path.abspath(cacheFilePath))
    (cacheFilesDir, cacheKey) = os.path.split(cacheFileDir)
    (cacheRootDir, cacheDirName) = os.path.split(cacheFilesDir)
    (cacheName, cacheExt) = os.path.splitext(cacheFile)

    if CacheFilenames.DIR_NAME_CACHE != cacheDirName:
        sys.stderr.write('WARNING: Cache directory name is "%s", expected "%s"' % \
            (cacheDirName, CacheFilenames.DIR_NAME_CACHE))
    if CacheFilenames.EXT_CACHE != cacheExt:
        sys.stderr.write('WARNING: Cache file extension is "%s", expected "%s"' % \
            (cacheExt, CacheFilenames.EXT_CACHE))

    return (cacheRootDir, cacheDirName, cacheKey, cacheName)

def unpickle(cacheFilePath, reportProgress = None):
    if reportProgress:
        reportProgress(0)

    percentsFileLoad = 5
    percentsUnpickle = 50
    percentsDecode = 100

    origData = _preWorkWithCache(cacheFilePath)

    output = open(cacheFilePath, 'rb')

    if reportProgress:
        reportProgress(percentsFileLoad)

    p = cPickle.Unpickler(output)
    p.persistent_load = pickle_helpers.persistent_unpickle
    ((dbKey, dbVersion), storedData) = p.load()

    if reportProgress:
        reportProgress(percentsUnpickle)

    try:
        v = storedData.get('__version__', 0)
    except AttributeError:
        v = 0
    if (dbKey, dbVersion) != (datacache.db_key(len(storedData)), v):
        raise Exception('Cache key and/or version mismatch. Are you trying to use ' + \
            'cache generated with another version of Parts?')

    progressReported = percentsUnpickle
    if isinstance(storedData, dict):
        rootDictKeysCount = sum([(1 if isinstance(storedData[key], dict) else 0) for key in storedData])
        rootDictKeysProcessed = 0
        for rootKey, rootVal in storedData.iteritems():
            if isinstance(rootVal, dict):
                for k, v in rootVal.iteritems():
                    if CacheFilenames.FILE_NODEINFO == split(cacheFilePath)[3] and rootKey in \
                            [NodeinfoKeys.KNOWN_NODES, NodeinfoKeys.KNOWN_PNODES]:
                        # This cache file section has complicated data structure so handle it
                        # in a special way
                        rootVal[k] = v['pinfo']

                rootDictKeysProcessed += 1
                if reportProgress:
                    progressMade = int(percentsUnpickle + (percentsDecode - percentsUnpickle) * \
                        float(rootDictKeysProcessed) / rootDictKeysCount)
                    if progressMade > progressReported:
                        reportProgress(progressMade)
                        progressReported = progressMade
    else:
        # Hmmm, something unexpected.
        raise Exception('Unexpected cache contents: {0}'.format(storedData))

    output.close()

    _postWorkWithCache(origData)

    if reportProgress:
        reportProgress(100)

    return storedData
