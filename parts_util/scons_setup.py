import os
import sys
import re

def getSupportedVersions():
    sconsVerSupported = []
    for sconsVer in ['2.1.0', '1.2.0']:
        # Try to find specific scons version...
        try:
            __getSconsPath(sconsVer)
            # ... found, add it to the list of supported ones
            sconsVerSupported.append(sconsVer)
        except:
            # ... not found, just ignore
            pass

    return sconsVerSupported

def setupDefault():
    try:
        __importAndPatch()
        # Import is performed successfully, it means that setup was made already
    except ImportError:
        # Environment is not updated. Get the highest version by default.
        sconsVerSupported = getSupportedVersions()
        if not sconsVerSupported:
            raise Exception('Unable to find scons installation')
        setup(sconsVerSupported[0])

def setup(sconsVersion):
    __setup(sconsVersion)
    __importAndPatch()

def __setup(sconsVersion):
    sconsPath = __getSconsPath(sconsVersion)
    sys.path.append(sconsPath)
    if not 'PYTHONPATH' in os.environ:
        os.environ['PYTHONPATH'] = sconsPath
    else:
        os.environ['PYTHONPATH'] += os.pathsep + sconsPath

def __importAndPatch():
    import SCons.Script.SConsOptions
    import SCons.Node
    import SCons.Script

    SCons.Node.Node.__repr__ = __reprSConsNodeNode
    SCons.Node.FS.Base.__repr__ = __reprSConsNodeFSBase
    SCons.Node.FS.FS.__repr__ = __reprSConsNodeFSFS
    SCons.Node.NodeInfoBase.__repr__ = __reprSCons_Node_NodeInfoBase

    # Workaround to make 'SCons.Script.GetOption' available even with dummy
    # implementation of SCons.Script.Main.OptionParser
    getOptionOrig = SCons.Script.GetOption
    def getOptionWrapper(name):
        value = getOptionOrig(name)
        if value is None:
            if 'parts_cache' == name:
                # This is to make parts load caches and create pnodes from them
                return True
            elif 'debug' == name:
                return []
        return value
    SCons.Script.GetOption = getOptionWrapper

# Returns path to scons installation. Raises exception if no scons was found
def __getSconsPath(version = None):
    if sys.platform == 'win32' or sys.platform == 'cli': # 'cli' is for IronPython
        pkgDirs = [
            sys.prefix,
            os.path.join(sys.prefix, 'Lib', 'site-packages')
        ]
    elif sys.platform.startswith('linux'):
        pkgDirs = [
            os.path.join(sys.prefix, 'lib'),
            os.path.join(sys.prefix, 'lib', 'python' + sys.version[:3], 'site-packages')
        ]
    elif sys.platform == 'darwin':
        raise Exception('%s is not supported yet' % sys.platform)
    else:
        raise Exception('%s is not supported' % sys.platform)

    # Key is scons version, value is path to scons dir
    sconsVer2Path = {}
    for pkgDir in pkgDirs:
        for dirName in os.listdir(pkgDir):
            if dirName.lower().startswith('scons'):
                mObj = re.search(r'scons-(?P<version>\d+(\.\w+)*)', dirName.lower())
                if mObj:
                    sconsVer2Path[mObj.group('version')] = os.path.join(pkgDir, dirName)

    if not sconsVer2Path:
        raise Exception('Unable to find scons installation')

    versionSelected = None
    if version == None:
        # Pick up the highest version
        # TODO: Use Parts version object to find the highest version
        versionSelected = sorted(sconsVer2Path.keys(), key = type(sconsVer2Path.keys()[0]).lower)[-1]
    elif version not in sconsVer2Path.keys():
        raise Exception('No scons with version %s installed' % str(version))
    else:
        versionSelected = version

    return sconsVer2Path[versionSelected]


def __reprSConsNodeNode(self):
    return "<{0}.{1} object str(self)={3}>".format(self.__module__,
        self.__class__.__name__, id(self), str(self))
    # OPEN: What is better to dump: str(self) or self.name?
    #return "<{0}.{1} object at 0x{2:x} {3}>".format(self.__module__,
    #    self.__class__.__name__, id(self), self.name)

def __reprSCons_Node_NodeInfoBase(self):
    # OPEN: Is it meaningful to dump "field_list"?
    return "<{0}.{1} object field_list={3}>".format(self.__module__,
        self.__class__.__name__, id(self), repr(self.field_list))

def __reprSConsNodeFSBase(self):
    return __reprSConsNodeNode(self)

def __reprSConsNodeFSFS(self):
    return "<{0}.{1} object pathTop={3}>".format(self.__module__,
        self.__class__.__name__, id(self), self.pathTop)
