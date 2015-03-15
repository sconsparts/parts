CALLBACK_FACTORY_NAME = 'createNodeCallbackObject'

class NodeCallback(object):
    def __init__(self):
        self._parserOptions = None
        self._args = None
        self._nodeinfoParser = None

    def preprocessNodes(self, parserOptions, args, nodeinfoParser, reportProgress):
        """
        'parserOptions' is cmd line parser options after cmd line arguments are parsed.
        'args' is a list with cmd line arguments (not including options).
        'nodeinfoParser' is an instance of cache_unpickle.NodeinfoParser with parsed cache info.
        'reportProgress' is a callback method to report percentage progress.
        """
        self._parserOptions = parserOptions
        self._args = args
        self._nodeinfoParser = nodeinfoParser

    def processNode(self, nodeId, nodeDict, nodeObj):
        """
        "nodeId" is:
         * path to node for node of "SCons.Node.FS.File" and "SCons.Node.FS.Dir" type.
         * alias for node of "SCons.Node.Alias.Alias" type.
         * value for node of "SCons.Node.Python.Value" type.

        "nodeDict" is a dictionary containing frequently used information for node. It can be empty.
        Currently the following key-value pairs can be present in it:
         * 'nodeInfo': instance of parts.pnode.scons_node_info.scons_node_info.
         * 'depends': list of strings representing dependencies for node. For Dir and File node types only.
         * 'partAlias': alias of part this node belongs to.

        "nodeObj" is an instance of node. It can be None.
        """
        pass

    def postprocessNodes(self, reportProgress):
        """
        'reportProgress' is a callback method to report percentage progress.
        """
        pass
