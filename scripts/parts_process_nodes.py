#!/usr/bin/env python

import sys
import os
import imp
import re
import copy

# TODO: Avoid copy-paste
try:
    # In 1st turn use parts_util from current working directory. In 2nd turn
    # use parts_util installed into Python
    from parts_util import *
except ImportError:
    # Not installed, try to find them near local instance of parts
    import _parts_util_setup_
    _parts_util_setup_.setup()

    from parts_util import *

if __name__ == '__main__':
    parser = options_common.getCommonParser(str(__file__))

    parser.add_option('--callback-module', dest = 'callbackModule',
        help = 'Path to python script containing the implementation of callback class for node processing')

    parser.add_option('--callback-factory', dest = 'callbackFactory', default = process_node_ifc.CALLBACK_FACTORY_NAME,
        help = 'Name of factory method to create an instance of callback class')

    nodeTypes = ['file', 'dir', 'value', 'alias']
    parser.add_option('--node-type', dest = 'nodeType', choices = nodeTypes, default = 'file',
        help = 'Type of nodes to process. Choices are %s. Default is "%s"' % (', '.join(nodeTypes), 'file'))

    parser.add_option('--nodes-root-dir', dest = 'nodesRootDir',
        help = 'Directory which paths of nodes are relative to. Applicable for "file" and "dir" node types only. ' + \
            'If not specified it is assumed to be directory where .parts_cache resides.')

    parser.add_option('--include-nodes', dest = 'includeNodes', metavar = 'REGEX',
        action = 'append', default = [], help = 'Filter in by specific nodes')

    parser.add_option('--include-extensions', dest = 'includeExtensions',
        action = 'append', default = [], help = 'Filter in by specific extensions. Applicable for "file" node type only')

    outputFormats = ['txt', 'xml']
    parser.add_option('-f', '--output-format', dest = 'outputFormat',
        choices = outputFormats, default = 'xml',
        help = 'Output format. Choices are %s. Default is "%s"' % (', '.join(outputFormats), 'xml'))

    #parser.add_option('--exclude-nodes', dest = 'excludeNodes', metavar = 'REGEX',
    #    action = 'append', default = [], help = 'Filter out by specific nodes')

    (options, args) = parser.parse_args()
    if len(args) == 0:
        parser.error('No path to cache file specified')
        sys.exit(1)
    elif len(args) > 1:
        print 'WARNING: Extra argument(s) {0} ignored.'.format(args[1:])

    datafile = args[0]
    datafileOrig = datafile
    if not os.path.isabs(datafile):
        datafile = os.path.join(os.getcwd(), datafile)
    if not os.path.exists(datafile) or not os.path.isfile(datafile):
        raise Exception('"%s" is not a valid file path' % datafileOrig)

    scons_setup.setup(options.sconsVersion)
    import SCons.Node
    nodeTypeToSconsType = {
        'file' : SCons.Node.FS.File,
        'dir' : SCons.Node.FS.Dir,
        'value' : SCons.Node.Python.Value,
        'alias' : SCons.Node.Alias.Alias
    }
    assert(sorted(nodeTypes) == sorted(nodeTypeToSconsType.keys()))

    # Parts redirects stderr and stdout, need to return them back
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    scriptPath = options.callbackModule
    if scriptPath is None:
        raise Exception('--callback-module option should be specified')
    scriptPathOrig = scriptPath
    if not os.path.isabs(scriptPath):
        scriptPath = os.path.join(os.getcwd(), scriptPath)
    if not os.path.exists(scriptPath) or not os.path.isfile(scriptPath):
        raise Exception('"%s" is not a valid file path' % scriptPathOrig)

    script = imp.load_source("script", scriptPath)
    if not hasattr(script, options.callbackFactory):
        raise Exception('Callback script "%s" does not contain factory function with name "%s"' % \
            (scriptPath, options.callbackFactory))

    factoryCallback = getattr(script, options.callbackFactory)

    stages = [
        'Loading data from cache',
        'Preprocessing nodes',
        'Processing nodes',
        'Postprocessing nodes'
    ]

    class ReportProgress(object):
        def __init__(self, stage):
            self.__stage = stage

        def __call__(self, percentsDone):
            sys.stderr.write('Step %d of %d. %s [%d%%]\r' % (self.__stage + 1,
                len(stages), stages[self.__stage], int(percentsDone)))
            sys.stderr.flush()

        def dumpFinalMessage(self):
            sys.stderr.write('Step %d of %d. %s [done]\n' % (self.__stage + 1,
                len(stages), stages[self.__stage]))
            sys.stderr.flush()

    nodeinfoParser = cache_unpickle.NodeinfoParser(datafile, ReportProgress(0))
    ReportProgress(0).dumpFinalMessage()

    aliases = nodeinfoParser.getAliases()
    includeRexes = [re.compile(i) for i in options.includeParts]
    excludeRexes = [re.compile(i) for i in options.excludeParts]

    nodeCallbackInstance = factoryCallback()

    argsCopy = copy.deepcopy(args)
    argsCopy[0] = datafile
    nodeCallbackInstance.preprocessNodes(options, argsCopy, nodeinfoParser, ReportProgress(1))
    ReportProgress(1).dumpFinalMessage()

    progressNodes = ReportProgress(2)
    for i in range(len(aliases)):
        alias = aliases[i]
        if any([i.search(alias) for i in excludeRexes]):
            continue
        if includeRexes and not any([i.search(alias) for i in includeRexes]):
            continue

        nodes = nodeinfoParser.getNodes(partAlias = alias, nodeType = nodeTypeToSconsType[options.nodeType],
            rootDir = options.nodesRootDir, extensions = options.includeExtensions, masks = options.includeNodes)
        for nodeId, nodeDict, nodeObj in nodes:
            nodeCallbackInstance.processNode(nodeId, nodeDict, nodeObj)

        progressNodes(100.0 * i / len(aliases))

    progressNodes.dumpFinalMessage()

    nodeCallbackInstance.postprocessNodes(ReportProgress(3))
    ReportProgress(3).dumpFinalMessage()
