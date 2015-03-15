from optparse import OptionParser, OptionGroup

import scons_setup
import cache_unpickle

def getCommonParser(callerModulePath):
    usageString = 'Usage: %s <path/to/cache/file>' % callerModulePath

    sconsVerSupported = scons_setup.getSupportedVersions()

    if not sconsVerSupported:
        raise Exception('Unable to find scons installation')

    # TODO: Consider switch to argparser (requires 2.7 python)
    # TODO: Consider to make <path/to/cache/file> optional and add option '--auto'
    # to automatic choosing of cache file from directory where script is invoked.
    parser = OptionParser(usageString)

    parser.add_option('--scons-version', dest = 'sconsVersion',
        choices = sconsVerSupported, default = sconsVerSupported[0],
        help = 'Scons version to work with. Choices are %s. Default is the highest "%s"' % \
            (', '.join(sconsVerSupported), sconsVerSupported[0]))

    parser.add_option('--include-parts', dest = 'includeParts', metavar = 'REGEX',
        action = 'append', default = [], help = 'Filter in by specific part aliases. ' + \
            'Applicable for "%s" cache file only' % cache_unpickle.CacheFilenames.FILE_NODEINFO)

    parser.add_option('--exclude-parts', dest = 'excludeParts', metavar = 'REGEX',
        action = 'append', default = [], help = 'Filter out by specific part aliases' + \
            'Applicable for "%s" cache file only' % cache_unpickle.CacheFilenames.FILE_NODEINFO)

    return parser
