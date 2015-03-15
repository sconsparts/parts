#!/usr/bin/env python

import sys
import os
import re
import pprint

# TODO: Avoid copy-paste
try:
    # Assume parts and parts_util are installed into Python
    from parts_util import *
except ImportError:
    # Not installed, try to find them near local instance of parts
    import _parts_util_setup_
    _parts_util_setup_.setup()

    from parts_util import *

indentIncrement = '  '

if __name__ == '__main__':
    parser = options_common.getCommonParser(str(__file__))

    parser.add_option('--include-nodes', dest = 'includeNodes', metavar = 'REGEX',
        action = 'append', default = [], help = 'Filter in by specific scons nodes' + \
            'Applicable for "%s" cache file only' % cache_unpickle.CacheFilenames.FILE_NODEINFO)

    parser.add_option('--exclude-nodes', dest = 'excludeNodes', metavar = 'REGEX',
        action = 'append', default = [], help = 'Filter out by specific scons nodes' + \
            'Applicable for "%s" cache file only' % cache_unpickle.CacheFilenames.FILE_NODEINFO)

    parser.add_option('--include-aliases', dest = 'includeAliases', metavar = 'REGEX',
        action = 'append', default = [], help = 'Filter in by specific aliases' + \
            'Applicable for "%s" cache file only' % cache_unpickle.CacheFilenames.FILE_NODEINFO)

    parser.add_option('--exclude-aliases', dest = 'excludeAliases', metavar = 'REGEX',
        action = 'append', default = [], help = 'Filter out by specific aliases' + \
            'Applicable for "%s" cache file only' % cache_unpickle.CacheFilenames.FILE_NODEINFO)

    (options, args) = parser.parse_args()
    if len(args) == 0:
        parser.error('No path to cache file specified')
        sys.exit(1)
    elif len(args) > 1:
        print 'WARNING: Extra argument(s) {0} ignored.'.format(args[1:])

    datafile = args[0]
    if not os.path.isfile(datafile):
        parser.error('Not a valid filepath: %s' % str(datafile))
        sys.exit(1)

    (cacheRootDir, cacheDirName, cacheKey, cacheName) = cache_unpickle.split(datafile)

    scons_setup.setup(options.sconsVersion)
    storedData = cache_unpickle.unpickle(datafile)
    assert(isinstance(storedData, dict))

    import parts.pnode.section_info as parts_pnode_section_info
    import parts.pnode.part_info as parts_pnode_part_info
    import parts.pnode.scons_node_info as parts_pnode_scons_node_info

    includeRexes = {
        cache_unpickle.NodeinfoKeys.KNOWN_PNODES: [re.compile(i) for i in options.includeParts],
        cache_unpickle.NodeinfoKeys.KNOWN_NODES: [re.compile(i) for i in options.includeNodes],
        cache_unpickle.NodeinfoKeys.ALIASES: [re.compile(i) for i in options.includeAliases],
    }
    excludeRexes = {
        cache_unpickle.NodeinfoKeys.KNOWN_PNODES: [re.compile(i) for i in options.excludeParts],
        cache_unpickle.NodeinfoKeys.KNOWN_NODES: [re.compile(i) for i in options.excludeNodes],
        cache_unpickle.NodeinfoKeys.ALIASES: [re.compile(i) for i in options.excludeAliases],
    }

    someFilteringExists = any([len(v) > 0 for k, v in includeRexes.iteritems()]) or \
        any([len(v) > 0 for k, v in excludeRexes.iteritems()])

    if someFilteringExists and cache_unpickle.CacheFilenames.FILE_NODEINFO != cacheName:
        raise Exception('Filtering options are supported only for "%s" cache file' % \
            cache_unpickle.CacheFilenames.FILE_NODEINFO)

    txtOutput = ''
    pp = pprint.PrettyPrinter()
    for rootKey, rootVal in storedData.iteritems():
        if (rootKey not in includeRexes.keys() or rootKey not in excludeRexes.keys()) and \
                cache_unpickle.CacheFilenames.FILE_NODEINFO == cacheName:
            raise Exception('Unknown key {0} in cache file'.format(rootKey))

        if someFilteringExists and len(includeRexes[rootKey]) == 0 and len(excludeRexes[rootKey]) == 0:
            continue

        txtOutput += "'{0}'".format(rootKey) + '\n'

        if isinstance(rootVal, dict):
            for k, v in rootVal.iteritems():
                if cache_unpickle.CacheFilenames.FILE_NODEINFO == cacheName and any([i.search(k) for i in excludeRexes[rootKey]]):
                    continue
                if cache_unpickle.CacheFilenames.FILE_NODEINFO == cacheName and \
                        includeRexes[rootKey] and not any([i.search(k) for i in includeRexes[rootKey]]):
                    continue

                if isinstance(v, (parts_pnode_section_info.section_info, parts_pnode_part_info.part_info,
                        parts_pnode_scons_node_info.scons_node_info)):
                    strType = v.__class__.__name__
                    val = {}
                    for member in v.__slots__:
                        if member.startswith('__'):
                            # Private member
                            val[member[2:]] = getattr(v, '_' + strType + member)
                        else:
                            val[member] = getattr(v, member)
                else:
                    val = v.__dict__ if hasattr(v, '__dict__') else v

                printLines = ["'{0}' = ".format(k)] + pp.pformat(val).splitlines()
                for line in printLines:
                    txtOutput += indentIncrement + line + '\n'
                txtOutput += '\n' # EOL
        else:
            txtOutput += indentIncrement + "'{0}'".format(rootVal) + '\n'
            txtOutput += '\n' # EOL

        txtOutput += '\n' # EOL

    # Parts redirects stderr and stdout, need to return them back
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    print txtOutput,
