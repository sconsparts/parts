import unittest
import shutil
import os
import sys
import parts.pieces
extract = sys.modules['<pieces>extract']
from parts import datacache
from parts import DefaultEnvironment

def rmdir(dirName):
    def onerror(func, path, exception):
        if exception[0] == os.error and exception[1].errno == 2 or \
           exception[0] == WindowsError and exception[1].winerror in (2,3):
            # Do not raise an error if the .parts.cache dir does not exists
            return None
        raise

    shutil.rmtree(dirName, onerror = onerror)

def clearTheCacheOnDisk():
    return rmdir('.parts.cache')

class TestExtract(unittest.TestCase):
    class MyEnv:
        def __init__(self):
            self.__env = {}
        def get(self, key, default = None):
            return self.__env.get(key, default)

        def arg2nodes(self, nodes, factory):
            return nodes

    class MyNode:
        def for_signature(self):
            return "MyNode"
        def get_csig(self):
            return "MyCSig"

    def setUp(self):
        self.env = TestExtract.MyEnv()
        self.node = TestExtract.MyNode()

        clearTheCacheOnDisk()
        rmdir('data')

    def test_zipGenerator(self):
        theList = ['data/',
                   'data/1/',
                   'data/1/4/',
                   'data/1/4/5/',
                   'data/1/4/5/5',
                   'data/1/4/4',
                   'data/1/1',
                   'data/1/2/',
                   'data/1/2/4',
                   'data/1/2/3/',
                   'data/1/2/3/5',
                   'data/1/2/3/3',
                   'data/1/2/2']
        self.assertEqual(set(theList), set(str(x) for x in extract.zipGenerator('./testdata/archives/data.zip')))

    def test_tarGenerator(self):
        theList = ['data',
                   'data/1',
                   'data/1/4',
                   'data/1/4/5',
                   'data/1/4/5/5',
                   'data/1/4/4',
                   'data/1/1',
                   'data/1/2',
                   'data/1/2/4',
                   'data/1/2/3',
                   'data/1/2/3/5',
                   'data/1/2/3/3',
                   'data/1/2/2']
        self.assertEqual(set(theList), set(str(x) for x in extract.tarGenerator('./testdata/archives/data.tar.gz')))

    def test_builder(self):
        env = DefaultEnvironment()
        self.assertEqual(['data/1/2/4'],
                [x.attributes.original_name for x in env.Extract('./testdata/archives/data.tar.gz',
                    EXTRACT_INCLUDES = ['data/1/2/4'])])
        self.assertEqual(['data/1/2/2'],
                [x.attributes.original_name for x in env.Extract('./testdata/archives/data.tar.bz2',
                    EXTRACT_INCLUDES = ['data/1/2/2'])])
        self.assertEqual(['data/1/4/4'],
                [x.attributes.original_name for x in env.Extract('./testdata/archives/data.zip',
                    EXTRACT_INCLUDES = ['data/1/4/4'])])

    def test_actions(self):
        env = DefaultEnvironment()
        def do_extract(archive, masks):
            for x in env.Extract(archive ,
                    EXTRACT_INCLUDES = masks, allow_duplicates = True):
                self.assertFalse(x.exists())
                x.prepare()
                x.build()
                x.built()
                self.assertTrue(x.exists())

        do_extract('./testdata/archives/data.tar.gz', ['data/1/2/4'])
        do_extract('./testdata/archives/data.zip', ['data/1/2/3/5'])
        do_extract('./testdata/archives/data.tar.bz2', ['data/1/2/3/3'])

# vim: set et ts=4 sw=4 ai :

