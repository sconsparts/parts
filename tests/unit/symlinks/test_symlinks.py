import unittest
import shutil
import os
import tempfile
import sys
import pytest

from parts import *

import SCons.Node.FS
import SCons.Errors

from parts.overrides.symlinks import os_symlink
from parts.overrides.symlinks import os_readlink


def _can_create_symlinks():
    """
    Check if the current system supports creating symlinks.
    On Windows, this requires proper privileges or Developer Mode.
    Returns True if symlinks are supported, False otherwise.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        test_target = os.path.join(tmpdir, 'test_target.txt')
        test_link = os.path.join(tmpdir, 'test_link')
        
        try:
            # Try to create a test file and symlink
            with open(test_target, 'w') as f:
                f.write('test')
            os_symlink(test_target, test_link, False)
            os.unlink(test_link)
            return True
        except (OSError, RuntimeError):
            # Symlinks not supported or permission denied
            return False


# Cache the result so we don't keep testing
SYMLINKS_SUPPORTED = _can_create_symlinks()


def rmdir(dirName):
    """Remove directory tree, handling errors gracefully."""
    def onerror(func, path, exception):
        if exception[0] == os.error and exception[1].errno == 2:
            # Do not raise an error if the directory does not exist
            return None
        raise

    shutil.rmtree(dirName, onerror=onerror)


class TestFileSymbolicLink(unittest.TestCase):
    """Test SCons FileSymbolicLink node type."""

    def test_envFileSymbolicLink(self):
        """Verify DefaultEnvironment creates FileSymbolicLink nodes."""
        env = DefaultEnvironment()
        assert isinstance(env.FileSymbolicLink('a'), SCons.Node.FS.FileSymbolicLink)
        assert isinstance(env.Entry('a'), SCons.Node.FS.FileSymbolicLink)
        with pytest.raises(TypeError):
            env.Dir('a')


@pytest.mark.skipif(not SYMLINKS_SUPPORTED, reason='Symlink creation not supported (requires admin/Dev Mode on Windows)')
class TestOsSymlink(unittest.TestCase):
    """Test os_symlink and os_readlink wrapper functions."""

    def setUp(self):
        self.addCleanup(self.cleanUp)
        self.workDir = tempfile.mkdtemp(dir='.')
        self.notlinkname = os.path.join(self.workDir, 'notlink')
        with open(self.notlinkname, 'w') as notlink:
            notlink.write('I am not link')
        self.linkname = os.path.join(self.workDir, 'link')

    def cleanUp(self):
        rmdir(self.workDir)

    def test_os_symlink(self):
        """Test that os_symlink rejects existing files and creates new symlinks."""
        with pytest.raises(OSError):
            os_symlink('target', self.notlinkname, False)
        os_symlink('target', self.linkname, False)
        os.unlink(self.linkname)

    def test_os_readlink(self):
        """Test that os_readlink reads symlink targets correctly."""
        with pytest.raises(OSError):
            os_readlink(self.notlinkname)
        os_symlink('target', self.linkname, False)
        assert os_readlink(self.linkname) == 'target'
        os.unlink(self.linkname)

# vim: set et ts=4 sw=4 ai ft=python :
