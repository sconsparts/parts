import unittest
from parts.filters import *
import SCons.Node
import os


class TestFilters(unittest.TestCase):

    def __createFile(self, fName, fDir):
        fs = SCons.Node.FS.get_default_fs()
        _dir = SCons.Node.FS.RootDir(fDir, fs)
        return SCons.Node.FS.File(fName, _dir, fs)

    def setUp(self):
        self.env = SCons.Script.Environment(tools=[])

    def test_hasFileExtension(self):
        """Test hasFileExtension: create 2 nodes (files) with different extensions"""
        dirname1 = "mydir"
        filename1 = "myfile.txt"
        myFile1 = self.__createFile(filename1, dirname1)

        dirname2 = "mydir2"
        filename2 = "myfile2.txt"
        myFile2 = self.__createFile(filename2, dirname2)

        hfe = hasFileExtension([dirname1 + os.sep + filename1])

        self.assertEqual(True, hfe(myFile1))
        self.assertEqual(False, hfe(myFile2))

    def test_HasPackageCatagory(self):
        """Test HasPackageCatagory: create 2 nodes (files) and set 'package' tag to one of them and assosiate 'category' value with this tag"""
        dirname1 = "mydir1"
        filename1 = "myfile1.txt"
        myFile1 = self.__createFile(filename1, dirname1)

        dirname2 = "mydir2"
        filename2 = "myfile2.txt"
        myFile2 = self.__createFile(filename2, dirname2)

        myCat = "my category"
        self.env.MetaTag(myFile1, 'package', category=myCat)

        hpc = HasPackageCatagory(myCat)
        self.assertEqual(True, hpc(myFile1))
        self.assertEqual(False, hpc(myFile2))
