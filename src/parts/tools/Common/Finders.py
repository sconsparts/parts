


import glob
import os
import re
import sys
from builtins import range

import SCons.Util
from SCons.Debug import logInstanceCreation


class PathFinder:
    '''
    Provides information
    '''

    def __init__(self, paths):
        if __debug__:
            logInstanceCreation(self)
        self.paths = paths

    def __call__(self):
        ret = None
        for pattern in self.paths:
            for p in glob.glob(pattern):
                if os.path.isdir(p):
                    ret = p
                    #print('Found default path [%s]' % (p))
                    return ret
                else:
                    #print('Did not find default path [%s]' % (p))
                    pass
        return ret


class EnvFinder:

    def __init__(self, keys, rel_path=None):
        if __debug__:
            logInstanceCreation(self)
        self.keys = keys
        self.rel_path = rel_path

    def __call__(self):

        for key in self.keys:
            ret = os.environ.get(key, None)
            if ret is None:
                #print('Shell value %s not found' % (key))
                pass
            elif os.path.isdir(ret):
                #print('Found shell value %s with value of %s' % (key,ret))
                pass
            else:
                #print('Path value of %s for varible of %s does not exists' % (ret,key))
                pass
        if self.rel_path is not None and ret is not None:
            ret = os.path.normpath(os.path.join(ret, self.rel_path))
        return ret


class RegFinder:

    def __init__(self, keys, rel_path=None):
        if __debug__:
            logInstanceCreation(self)
        self.keys = keys
        self.rel_path = rel_path

        if self.keys is None or self.keys == []:
            print("RegFinder was given not passed any values to find")

    def read_reg(self, value):
        ret = SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE, value)
        return ret[0]

    def __call__(self):
        ret = None
        for key in self.keys:
            try:
                ret = self.read_reg(key)
                #print('Found key in registry: %s' % ret)
                break
            except WindowsError as e:
                #print('Did not find key %s in registry' % (ret))
                ret = None
        if self.rel_path is not None and ret is not None:
            ret = os.path.normpath(os.path.join(ret, self.rel_path))
        return ret


# special windows only finder that looks up data based on how MSI files
# store information in the registry hive. On non windows system this is
# an empty object that does nothing
if sys.platform == 'win32':
    import parts.platformspecific.win32.msi as msi

    class MsiFinder:
        """
        This class uses MSI API to find tools installed on the system.
        When the objects __call__ method is called the finder reads list
        of apps installed, scans it comparing product name's to specified
        regular expression. When a match is found the code checks whether
        the specified executable is realy on the system and returns
        path to directory where it is installed.
        """

        def __init__(self, productNamePattern, component, upDirs=None, subDir=None):
            """
            @type  productNamePattern: string
            @param productNamePattern: Python RegExp compatilble pattern to match against product name
            @type  component: string
            @param component: String representing MSI database component name of executable of interest.
                              For example, CandleBinaries is component name for candle.exe from Wix package,
                              PythonExe is the name of python.exe component from ActiveState Python package.
            @type  upDirs: integer or None
            @param upDirs: A number of path entries to delete from component path to get install path.
                           Assume upDirs is 2 and path to component is 'foo/bar/bar/component' then path
                           returned by MsiFinder.__call__ will return 'foo/'.
            @type  subDir: string or None
            @param subDir: a string to be appended to path found in MSI to form a full path to a directory
            """
            self.__pattern = re.compile(productNamePattern)
            self.__component = re.compile(component)
            self.__upDirs = upDirs
            self.__subDir = subDir

        def __iter__(self):
            """
            Method to make MsiFinder objects look like sequence type instance.
            """
            yield self
            raise StopIteration

        def __call__(self):
            """
            The method is called by Parts infrastructure to determine whether particular tool is installed
            on the system.
            """
            try:
                return self.__path
            except AttributeError:
                for product in msi.allProducts():
                    if self.__pattern.match(product.ProductName):
                        db = msi.Database(product.LocalPackage, msi.MSIDBOPEN_READONLY)
                        view = db.openView("select Component, ComponentId from Component")
                        for componentName, componentID in view:
                            if self.__component.match(componentName):
                                state, path = product.getComponentPath(componentID)
                                path = os.path.dirname(path)
                                if state == msi.INSTALLSTATE_LOCAL and os.path.exists(path):
                                    if self.__upDirs is not None:
                                        for i in range(self.__upDirs):
                                            path = os.path.dirname(path)
                                    if self.__subDir:
                                        path = os.path.join(path, self.__subDir)
                                    self.__path = path
                                    return self.__path
                self.__path = None
            return self.__path

        def resolve(self, version):
            return self()

        def resolve_version(self, version):
            return version

else:
    class MsiFinder:

        def __init__(self, *lst, **kw):
            pass

        def __call__(self):
            return None


class ScriptFinder:

    def __init__(self, name, args=None, keep=None, remove=None):
        if __debug__:
            logInstanceCreation(self)
        self.name = name
        self.args = args
        self.keep = keep
        self.remove = remove

    def __call__(self, env):
        # get the full path
        p = env.subst(self.name)
        p = os.path.normpath(p)
        if os.path.isfile(p):
            return p
        return None
