import unittest
import shutil
import os
import tempfile

from parts import *

import SCons.Node.FS
import SCons.Errors


def rmdir(dirName):
    def onerror(func, path, exception):
        if exception[0] == os.error and exception[1].errno == 2 or \
           exception[0] == WindowsError and exception[1].winerror in (2, 3):
            # Do not raise an error if the .parts.cache dir does not exists
            return None
        raise

    shutil.rmtree(dirName, onerror=onerror)


def clearTheCacheOnDisk():
    return rmdir('.parts.cache')


class TestFileSymbolicLink(unittest.TestCase):

    def setUp(self):
        self.addCleanup(self.cleanUp)

    def cleanUp(self):
        clearTheCacheOnDisk()

    def test_envFileSymbolicLink(self):
        self.assertIsInstance(DefaultEnvironment().FileSymbolicLink('a'), SCons.Node.FS.FileSymbolicLink)
        self.assertIsInstance(DefaultEnvironment().Entry('a'), SCons.Node.FS.FileSymbolicLink)
        self.assertRaises(TypeError, DefaultEnvironment().Dir, 'a')

from parts.overrides.symlinks import os_symlink
from parts.overrides.symlinks import os_readlink


class TestOsSymlink(unittest.TestCase):

    def setUp(self):
        self.addCleanup(self.cleanUp)
        self.workDir = tempfile.mkdtemp(dir='.')
        self.notlinkname = os.path.join(self.workDir, 'notlink')
        with open(self.notlinkname, 'w') as notlink:
            print >> notlink, 'I am not link'
        self.linkname = os.path.join(self.workDir, 'link')

    def cleanUp(self):
        rmdir(self.workDir)

    def test_os_symlink(self):
        self.assertRaises(OSError, os_symlink, 'target', self.notlinkname, False)
        os_symlink('target', self.linkname, False)
        os.unlink(self.linkname)

    def test_os_readlink(self):
        self.assertRaises(OSError, os_readlink, self.notlinkname)
        os_symlink('target', self.linkname, False)
        self.assertEqual(os_readlink(self.linkname), 'target')
        os.unlink(self.linkname)

# vim: set et ts=4 sw=4 ai ft=python :
