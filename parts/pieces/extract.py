import os
import zipfile
import tarfile
import errno
import contextlib

import SCons.Builder
import SCons.Action
import SCons.Environment
import SCons.Node.FS
import ctypes
from parts.common import matches
from parts import api
from parts.overrides import symlinks

try:
    os_link = os.link
except AttributeError:
    try:
        CreateHardLinkW = ctypes.windll.kernel32.CreateHardLinkW
        os_link = lambda src, dst: CreateHardLinkW(unicode(src), unicode(dst), None)
    except AttributeError:
        def os_link(src, dst):
            raise OSError("Don't know how to make hard link on Windows NT")

__namesCache = {}
"""
__namesCache contains info of form:
{
    'path/to/archive.zip': {'path/inside/archive': (indexInTheArchive, isdir, issym)}
}
"""


def _getNameForKey(fileNode):
    '''
    Value returned by this function will be used as an ID for fileNode.
    '''
    if fileNode.exists():
        return fileNode.abspath
    elif id(fileNode) != id(fileNode.srcnode()) and fileNode.srcnode().exists():
        return fileNode.srcnode().abspath
    return str(fileNode)


def getNodesFromCache(fileNode, generator, env):
    try:
        nodeNames = __namesCache[_getNameForKey(fileNode)]
    except KeyError:
        __namesCache[_getNameForKey(fileNode)] = nodeNames = \
            dict((str(item), (item.index, item.isdir(), item.issym()))
                 for item in generator(fileNode))

    nodes = []
    includes = [str(x) for x in env.Flatten(env.subst_list('$EXTRACT_INCLUDES',
                                                           source=[fileNode.get_subst_proxy()], target=[])) if x]
    excludes = [str(x) for x in env.Flatten(env.subst_list('$EXTRACT_EXCLUDES',
                                                           source=[fileNode.get_subst_proxy()], target=[])) if x]

    if not includes:
        includes = ['*']
    if not excludes:
        excludes = []

    for nodeName, (index, isdir, issym) in nodeNames.iteritems():
        if (not isdir) and matches(nodeName, includes, excludes):
            node = env.Entry(nodeName)
            if issym:
                symlinks.ensure_node_is_symlink(node)
            node.attributes.archive_index = index
            node.attributes.original_name = nodeName
            nodes.append(nodeName)

    return nodes


class _ArcInfoProxy(object):
    __slots__ = ['_index', '_item', '_arc', '__init__', '__str__', 'open',
                 '_extract_file', '_extract_dir', '_extract_symlink', 'index',
                 'isdir', 'islnk', 'issym', 'linkname', 'extract']

    def __init__(self, archive, archiveItem, index):
        self._arc = archive
        self._item = archiveItem
        self._index = index

    def __str__(self):
        return 'None'

    @property
    def index(self):
        return self._index

    def open(self):
        raise AttributeError("_ArcInfoProxy.open is not implemented")

    def isdir(self):
        return False

    def islnk(self):
        return False

    def issym(self):
        return False

    @property
    def linkname(self):
        return None

    def _extract_symlink(self, nodes):
        for node in nodes:
            try:
                symlinks.os_symlink(self.linkname, node.abspath, False)
            except (OSError, IOError):
                try:
                    os.unlink(node.abspath)
                except OSError as err:
                    if err.errno != errno.ENOENT:
                        raise
                symlinks.os_symlink(self.linkname, node.abspath, False)
            symlinks.ensure_node_is_symlink(node)

    def _extract_dir(self, nodes):
        for node in nodes:
            if not os.path.exists(node.abspath):
                try:
                    os.makedirs(node.abspath)
                except OSError:
                    pass

    def _extract_file(self, nodes):
        '''
        Writes contents of self._item to nodes specified.
        '''

        targets = []
        try:
            for node in nodes:
                targets.append(open(str(node), 'wb'))

            source = self.open()
            try:
                while True:
                    buf = source.read(16384)
                    if not buf:
                        break
                    for target in targets:
                        target.write(buf)
            finally:
                source.close()
                del source
        finally:
            for target in targets:
                target.close()

    def extract(self, nodes):
        if self.isdir():
            self._extract_dir(nodes)
        elif self.issym():
            self._extract_symlink(nodes)
        else:
            self._extract_file(nodes)


class _TarInfoProxy(_ArcInfoProxy):
    __slots__ = ['__init__', '__str__', 'open', 'isdir', 'issym', 'extract', 'linkname']

    def __init__(self, tarfile, tarinfo, index):
        super(self.__class__, self).__init__(tarfile, tarinfo, index)

    def __str__(self):
        return self._item.name

    def open(self):
        return self._arc.extractfile(self._item)

    def isdir(self):
        return self._item.isdir()

    def issym(self):
        return self._item.issym()

    @property
    def linkname(self):
        return self._item.linkname

    def extract(self, nodes):
        super(self.__class__, self).extract(nodes)

        # Tar file contains some additional info on each file.
        # Update it as well.
        actions = [self._arc.chown]
        if not self.issym():
            actions += [self._arc.chmod, self._arc.utime]

        for node in nodes:
            for action in actions:
                action(self._item, node.abspath)


class _ZipInfoProxy(_ArcInfoProxy):
    __slots__ = ['__init__', '__str__', 'open', 'isdir']

    def __init__(self, zipfile, zipinfo, index):
        super(self.__class__, self).__init__(zipfile, zipinfo, index)

    def __str__(self):
        return self._item.filename

    def open(self):
        return self._arc.open(self._item)

    def isdir(self):
        return self._item.filename[-1] == '/'


def zipGenerator(source):
    with contextlib.closing(zipfile.ZipFile(str(source))) as zfile:
        index = -1
        for zinfo in zfile.infolist():
            index += 1
            yield _ZipInfoProxy(zfile, zinfo, index)


def emitterUnzip(target, source, env):
    target = getNodesFromCache(source[0], zipGenerator, env)

    return target, source


def tarGenerator(source):
    with contextlib.closing(tarfile.open(str(source))) as tfile:
        index = -1
        for info in tfile:
            index += 1
            yield _TarInfoProxy(tfile, info, index)


def emitterUntar(target, source, env):
    target = getNodesFromCache(source[0], tarGenerator, env)

    return target, source


def actionUnpack(generator, target, source, env):
    output = env._get_part_log_mapper()
    id = output.TaskStart("Extracting from {0}".format(source[0].path))
    try:
        target.sort(key=lambda x: x.attributes.archive_index)
        tgtIter = iter(target)
        arcIter = generator(source[0])
        try:
            arcItem = arcIter.next()

            tgtItem = tgtIter.next()
            while True:
                while tgtItem.attributes.archive_index < arcItem.index:
                    tgtItem = tgtIter.next()
                while tgtItem.attributes.archive_index > arcItem.index:
                    try:
                        arcItem = arcIter.next()
                    except StopIteration:
                        # Oops! There are no more items in the archive but we still
                        # have targets to be extracted
                        raise SCons.Errors.UserError('Unexpected end of archive')
                nodes = []
                while tgtItem.attributes.archive_index == arcItem.index:
                    try:
                        nodes.append(tgtItem)
                        tgtItem = tgtIter.next()
                    except StopIteration:
                        # We have iterated through all the targets
                        # now extract them and return
                        arcItem.extract(nodes)
                        return None
                arcItem.extract(nodes)
        except StopIteration:
            pass
        return None
    finally:
        output.TaskEnd(id, 0)


def batch_key(action, env, target, source):
    return _getNameForKey(source[0])

actionUntar = lambda target, source, env: actionUnpack(tarGenerator, target, source, env)
actionUnzip = lambda target, source, env: actionUnpack(zipGenerator, target, source, env)

api.register.add_builder('Extract',
                         SCons.Builder.Builder(
                             action={
                                 '.zip': SCons.Action.Action(actionUnzip, cmdstr="Extracting from $SOURCE", batch_key=batch_key),
                                 '.gz': SCons.Action.Action(actionUntar, cmdstr="Extracting from $SOURCE", batch_key=batch_key),
                                 '.bz2': SCons.Action.Action(actionUntar, cmdstr="Extracting from $SOURCE", batch_key=batch_key)
                             },
                             emitter={
                                 '.zip': emitterUnzip,
                                 '.gz': emitterUntar,
                                 '.bz2': emitterUntar
                             },
                             prefix='',
                             suffic='',
                             src_suffix=['.zip', '.gz', '.bz2'],
                             target_factory=SCons.Node.FS.Entry,
                         )
                         )

# vim: set et ts=4 ai :
