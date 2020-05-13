'''
This module introduces FileSymbolicLink class to SCons.Node.FS module as well as
FileSymbolicLink methods to SCons.Script.Environment, SCons.Node.FS.FS, SCons.Node.FS.Dir,
and SCons.Node.FS.File classes.

There is also env.SymLink builder is introduced here
'''


import ctypes
import os

import parts.api as api
import parts.common as common
import parts.metatag as metatag
import SCons.Node.FS
from parts.core import util
from SCons.Debug import logInstanceCreation
from SCons.Scanner import Scanner
from SCons.Script.SConscript import SConsEnvironment

# Begin OS level support for symbolic links
try:
    from os import symlink as _os_symlink

    def os_symlink(linkto, linkname, isdir): return _os_symlink(linkto, linkname)
except ImportError:
    # Some magic numbers are needed. Their names can be found in MSDN.
    FSCTL_SET_REPARSE_POINT = 589988
    IO_REPARSE_TAG_SYMLINK = 0xA000000C
    REPARSE_DATA_BUFFER_HEADER_SIZE = 8
    GENERIC_WRITE = 0x40000000
    CREATE_NEW = 1
    CREATE_ALWAYS = 2
    OPEN_EXISTING = 3
    FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    FORMAT_MESSAGE_ALLOCATE_BUFFER = 0x00000100
    FORMAT_MESSAGE_FROM_SYSTEM = 0x00001000
    FORMAT_MESSAGE_IGNORE_INSERTS = 0x00000200
    TOKEN_ADJUST_PRIVILEGES = 0x00000020
    TOKEN_QUERY = 0x00000008
    SE_PRIVILEGE_ENABLED = 0x00000002

    class LUID(ctypes.Structure):
        _fields_ = [('LowPart', ctypes.c_ulong),
                    ('HighPart', ctypes.c_long)]

    class LUID_AND_ATTRIBUTES(ctypes.Structure):
        _pack_ = 4
        _fields_ = [('Luid', LUID),
                    ('Attributes', ctypes.c_ulong)]

    class TOKEN_PRIVILEGES(ctypes.Structure):
        _fields_ = [('PrivilegeCount', ctypes.c_ulong),
                    ('Privileges', LUID_AND_ATTRIBUTES * 1)]

    class Privilege:
        """
        Context class to temporary elevate privilege.
        """

        def __init__(self, privilegeName):
            if __debug__:
                logInstanceCreation(self, 'parts.overrides.symlinks.Privilege')
            self.token = None
            self.savedState = None
            self.privilegeLuid = LUID()
            if not ctypes.windll.advapi32.LookupPrivilegeValueA(
                    ctypes.c_void_p(), ctypes.c_char_p(privilegeName),
                    ctypes.byref(self.privilegeLuid)):
                raise createWindowsError()

        def __enter__(self):
            token = ctypes.c_void_p()
            if ctypes.windll.advapi32.OpenProcessToken(
                    ctypes.c_void_p(ctypes.windll.kernel32.GetCurrentProcess()),
                    TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
                    ctypes.byref(token)):
                self.token = token
                self.savedState = None
                privileges = TOKEN_PRIVILEGES()
                privileges.PrivilegeCount = 1
                privileges.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
                privileges.Privileges[0].Luid = self.privilegeLuid

                savedState = TOKEN_PRIVILEGES()
                dwReturned = ctypes.c_ulong(ctypes.sizeof(savedState))
                if ctypes.windll.advapi32.AdjustTokenPrivileges(self.token, 0,
                                                                ctypes.byref(privileges), ctypes.sizeof(privileges),
                                                                ctypes.byref(savedState), ctypes.byref(dwReturned)) and \
                        ctypes.GetLastError() == 0:
                    self.savedState = savedState
            else:
                self.token = None
                raise createWindowsError()
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            if self.token:
                if self.savedState:
                    ctypes.windll.advapi32.AdjustTokenPrivileges(self.token, ctypes.c_long(),
                                                                 ctypes.byref(self.savedState), ctypes.sizeof(self.savedState),
                                                                 ctypes.c_void_p(), ctypes.c_void_p())
                ctypes.windll.kernel32.CloseHandle(self.token)

    def createWindowsError(path=None):
        """
        Utility function to create a human-readable WindowsError exception.
        @param path: Optional C{string} specifying path to file/directory operation on
            which caused the exception.
        """
        errorCode = ctypes.GetLastError()
        message = ctypes.FormatError(errorCode)
        if message:
            if path:
                return WindowsError(errorCode, message, path)
            return WindowsError(errorCode, message)
        return WindowsError(errorCode)

    # Some data types
    class SymbolicLinkReparseBuffer(ctypes.Structure):
        """
        Represents a Microsoft reparse point record layout.
        """
        _fields_ = [
            ('ReparseTag', ctypes.c_ulong),
            ('ReparseDataLength', ctypes.c_ushort),
            ('Reserved', ctypes.c_ushort),
            # Head end
            ('SubstituteNameOffset', ctypes.c_ushort),
            ('SubstituteNameLength', ctypes.c_ushort),
            ('PrintNameOffset', ctypes.c_ushort),
            ('PrintNameLength', ctypes.c_ushort),
            ('Flags', ctypes.c_ulong),
            ('PathBuffer', ctypes.c_ushort * 1)
        ]
    PSymbolicLinkReparseBuffer = ctypes.POINTER(SymbolicLinkReparseBuffer)
    SYMLINK_PRIVILEGE_NAME = 'SeCreateSymbolicLinkPrivilege'
    try:
        CreateSymbolicLink = ctypes.windll.kernel32.CreateSymbolicLinkW

        def os_symlink(linkto, linkname, isdir):
            with Privilege(SYMLINK_PRIVILEGE_NAME):
                if not CreateSymbolicLink(str(linkname), str(linkto),
                                          1 if isdir else 0):
                    raise createWindowsError(path=linkname)
    except AttributeError:
        # This means we are running on the Windows older than Vista which has no
        # CreateSymbolicLink API. Let's implement it.

        # The following code was written under impression of reading FAR Manager code.
        # See http://farmanager.com/svn/trunk/unicode_far/flink.cpp
        def _formatLinkBuffer(target):
            """
            Creates a byte string to be put on file system to represent a reparse point

            @param target: C{string} representing a symbolic link (junction) target.
            """
            printName = str(target)
            sysName = str(target if not os.path.isabs(target) else r'\\??\\' + target)

            buffsize = ctypes.sizeof(SymbolicLinkReparseBuffer) + (
                len(printName) + len(sysName)) * 2

            result = ctypes.create_string_buffer(buffsize)
            pBuffer = ctypes.cast(ctypes.pointer(result), PSymbolicLinkReparseBuffer).contents
            pBuffer.Reserved = 0
            pBuffer.Flags = 1
            pBuffer.ReparseTag = IO_REPARSE_TAG_SYMLINK

            pBuffer.PrintNameOffset = 0
            pBuffer.PrintNameLength = len(printName) * ctypes.sizeof(ctypes.c_wchar)

            p = ctypes.cast(ctypes.pointer(pBuffer.PathBuffer), ctypes.c_void_p)
            ctypes.memmove(p, ctypes.c_wchar_p(printName),
                           ctypes.sizeof(ctypes.c_wchar) * len(printName))

            pBuffer.SubstituteNameOffset = pBuffer.PrintNameLength
            pBuffer.SubstituteNameLength = len(sysName) * ctypes.sizeof(ctypes.c_wchar)

            p = ctypes.cast(ctypes.cast(ctypes.pointer(pBuffer.PathBuffer),
                                        ctypes.c_void_p).value + pBuffer.SubstituteNameOffset,
                            ctypes.c_void_p)
            ctypes.memmove(p, ctypes.c_wchar_p(sysName),
                           ctypes.sizeof(ctypes.c_wchar) * len(sysName))

            pBuffer.ReparseDataLength = buffsize - REPARSE_DATA_BUFFER_HEADER_SIZE

            return result, buffsize

        def os_symlink(linkto, linkname, isdir):
            """
            C{os.symlink} implementation for Microsoft Windows

            @param linkto: C{string} representing link target name
            @param linkname: Link name C{string}
            @param isdir: C{boolean} determining whether the symlink points to directory or
                to a file.
            """
            with Privilege(SYMLINK_PRIVILEGE_NAME):
                ctypes.SetLastError(0)
                if isdir:
                    if not ctypes.windll.kernel32.CreateDirectoryA(linkname):
                        raise createWindowsError(path=linkname)
                    handleFlag = OPEN_EXISTING
                else:
                    handleFlag = CREATE_NEW
                handle = ctypes.windll.kernel32.CreateFileA(linkname, GENERIC_WRITE, 0,
                                                            ctypes.c_void_p(), handleFlag,
                                                            FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_BACKUP_SEMANTICS,
                                                            ctypes.c_void_p())
                if handle < 0:
                    raise createWindowsError(path=linkname)
                try:
                    buffer, size = _formatLinkBuffer(linkto)
                    dwreturned = ctypes.c_ulong()
                    if not ctypes.windll.kernel32.DeviceIoControl(
                            handle, FSCTL_SET_REPARSE_POINT, buffer, size, ctypes.c_void_p(), 0,
                            ctypes.byref(dwreturned), ctypes.c_void_p()):
                        raise createWindowsError(path=linkname)
                finally:
                    ctypes.windll.kernel32.CloseHandle(handle)
try:
    from os import readlink as os_readlink
except ImportError:
    # Some magic numbers from Windows headers
    FSCTL_GET_REPARSE_POINT = 589992
    FILE_ATTRIBUTE_REPARSE_POINT = 1024
    MAXIMUM_REPARSE_DATA_BUFFER_SIZE = 16384
    INVALID_FILE_ATTRIBUTES = -1
    INVALID_HANDLE_VALUE = -1
    GENERIC_READ = 0x80000000

    def os_readlink(name):
        """
        C{os.readlink} implementation for Microsoft Windows

        @param name: Symbolic link name.
        """
        attrs = ctypes.windll.kernel32.GetFileAttributesA(name)
        if attrs == INVALID_FILE_ATTRIBUTES or (attrs & FILE_ATTRIBUTE_REPARSE_POINT == 0):
            raise createWindowsError(path=name)
        h = ctypes.windll.kernel32.CreateFileA(name, GENERIC_READ, 0, ctypes.c_void_p(),
                                               OPEN_EXISTING, FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_BACKUP_SEMANTICS,
                                               ctypes.c_void_p())
        if h == INVALID_HANDLE_VALUE:
            raise createWindowsError(path=name)
        try:
            buffer = ctypes.create_string_buffer(MAXIMUM_REPARSE_DATA_BUFFER_SIZE)
            dwreturned = ctypes.c_ulong()
            if not ctypes.windll.kernel32.DeviceIoControl(
                    h, FSCTL_GET_REPARSE_POINT, ctypes.c_void_p(), 0, buffer,
                    ctypes.sizeof(buffer), ctypes.byref(dwreturned), ctypes.c_void_p()):
                raise createWindowsError(path=name)
        finally:
            ctypes.windll.kernel32.CloseHandle(h)

        content = ctypes.cast(buffer, PSymbolicLinkReparseBuffer).contents
        if not content.ReparseTag == IO_REPARSE_TAG_SYMLINK:
            raise createWindowsError(path=name)
        return ctypes.wstring_at(ctypes.cast(content.PathBuffer,
                                             ctypes.c_void_p).value + content.PrintNameOffset,
                                 content.PrintNameLength / 2)

# End of OS level support for symbolic links


class FileSymbolicLink(SCons.Node.FS.File):
    """
    Node class representing symbolic links. The class introduces C{linkto} property.
    The property represents a value a call to os.readlink would return for the C{self.path}
    specified as its argument.
    """
    __slots__ = []
    """
    slots to be compatible with scons newer than 2.3.0
    """
    __linktos__ = {}
    """
    This global dictionary will hold _linkto values for each FileSymbolicLink instance:
    __linktos__[node.abspath] = _linkto. See the linkto property getter for reference
    """

    def __init__(self, name, directory, fs):
        if __debug__:
            logInstanceCreation(self, 'parts.overrides.symlinks.FileSymbolicLink')
        SCons.Node.FS.File.__init__(self, name, directory, fs)

    @property
    def linkto(self):
        """
        C{FileSymbolicLink.linkto} property getter function.
        """
        try:
            return self.__linktos__[self.abspath]
        except KeyError:
            try:
                self.__linktos__[self.abspath] = value = os_readlink(self.abspath)
                return value
            except (OSError, IOError):
                return None

    @linkto.setter
    def linkto(self, value):
        """
        C{FileSymbolicLink.linkto} property setter function.
        """
        if value is None:
            try:
                del self.__linktos__[self.abspath]
            except KeyError:
                pass
            return
        self.__linktos__[self.abspath] = value

    def stat(self):
        """
        This function is mostly the same as C{SCons.Node.FS.File.stat} except it uses C{os.lstat} instead of C{os.stat}
        """
        try:
            return self._memo['stat']
        except KeyError:
            try:
                result = os.lstat(self.abspath)
            except os.error:
                return None
            self._memo['stat'] = result
        return result

    def get_contents(self):
        """
        Returns C{FileSymbolicLink.linkto} property value.
        """
        return self.linkto.encode("utf-8") if self.linkto else b''

    def srcnode(self):
        """
        There is only one difference between this function and SCons.Node.FS.File.srcnode one.
        It calls ensure_node_is_symlink instead of self.must_be_same function.
        """
        srcdir_list = self.dir.srcdir_list()
        if srcdir_list:
            srcnode = srcdir_list[0].Entry(self.name)
            ensure_node_is_symlink(srcnode, self)
            return srcnode
        return self

    def must_be_same(self, klass):
        if klass is SCons.Node.FS.File:
            return
        return SCons.Node.FS.File.must_be_same(self, klass)


SCons.Node.FS.FileSymbolicLink = FileSymbolicLink


def _def_SCons_Node_FS_FS_FileSymbolicLink(klass):
    def FileSymbolicLink(self, name, directory=None, create=1):
        return self._lookup(name, directory, SCons.Node.FS.FileSymbolicLink, create)
    klass.FileSymbolicLink = FileSymbolicLink


_def_SCons_Node_FS_FS_FileSymbolicLink(SCons.Node.FS.FS)


def _def_SCons_Node_FS_Dir_FileSymbolicLink(klass):
    def FileSymbolicLink(self, name):
        return self.fs.FileSymbolicLink(name, self)
    klass.FileSymbolicLink = FileSymbolicLink


_def_SCons_Node_FS_Dir_FileSymbolicLink(SCons.Node.FS.Dir)


def _def_SCons_Node_FS_File_FileSymbolicLink(klass):
    def FileSymbolicLink(self, name):
        return self.dir.FileSymbolicLink(name)
    klass.FileSymbolicLink = FileSymbolicLink


_def_SCons_Node_FS_File_FileSymbolicLink(SCons.Node.FS.File)


def _def_SConsEnvironment_FileSymbolicLink(klass):
    def FileSymbolicLink(self, name, *args, **kw):
        s = self.subst(name)
        if SCons.Util.is_Sequence(s):
            result = []
            for e in s:
                result.append(self.fs.FileSymbolicLink(e, *args, **kw))
            return result
        return self.fs.FileSymbolicLink(s, *args, **kw)
    klass.FileSymbolicLink = FileSymbolicLink


_def_SConsEnvironment_FileSymbolicLink(SConsEnvironment)


def ensure_node_is_symlink(node, template=None):
    """
    Checks if the node is a symlink, converts it to a symlink based on the template.
    """
    if isinstance(node, SCons.Node.FS.Base):
        if not isinstance(node, SCons.Node.FS.FileSymbolicLink):
            node.__class__ = SCons.Node.FS.FileSymbolicLink
            node._morph()

            if template is not None:
                node.linkto = template.linkto
    return node


def _wrap_MetaTag(MetaTag):
    def call(MetaTag, nodes, ns, **kw):
        def _warning(k):
            api.output.verbose_msg(['warning'], '{0} meta-tag usage is deprecated. Consider using SymLink() function'.format(k))

        def _convert_nodes(nodes, linkto):
            """
            Convert each node of nodes into a FileSymbolicLink instance.
            Check if the node is built only from one child using CCopy builder.
            If so convert the child too.
            """
            for node in common.make_list(nodes):
                ensure_node_is_symlink(node)

                api.output.verbose_msg('symlinks',
                                       "Updating SymLink node {node} pointing to {linkto} to point to {linktonew}".format(
                                           node=node, linkto=node.linkto, linktonew=linkto))
                node.linkto = linkto

                # This node can be copied only as a FileSymbolicLink.
                # Ensure all its CCopy targets are symlinks too.
                try:
                    for target in node.attributes.copiedas:
                        ensure_node_is_symlink(target)
                except AttributeError:
                    pass

                if node.sources and len(node.sources) == 1 and node.has_builder():
                    bld = node.get_builder()
                    if hasattr(bld, 'name') and bld.name == 'CCOPY':
                        # Convert source nodes into a SymLink nodes
                        _convert_nodes(node.sources, linkto)

        if 'SymLink' in kw:
            _warning('SymLink')
            linkto = kw.pop('SymLink')
            _convert_nodes(common.make_list(nodes), linkto)

        if 'SymLinkMakeDummyFile' in kw:
            _warning('SymLinkMakeDummyFile')
            kw.pop('SymLinkMakeDummyFile')
        if kw and MetaTag:
            return MetaTag(nodes, ns, **kw)
        return None
    return lambda nodes, ns='meta', **kw: call(MetaTag, nodes, ns, **kw)


metatag.MetaTag = _wrap_MetaTag(metatag.MetaTag)


def _wrap_SCons_Node_FS_Entry_disambiguate(disambiguate):
    def call(self, must_exist=None):
        if self.islink() and self.__class__ != FileSymbolicLink:
            is_file = self.__class__ == SCons.Node.FS.File
            self.__class__ = FileSymbolicLink
            self._morph()
            if not is_file:
                self.clear()
            else:
                if "exists" in self._memo:
                    del self._memo["exists"]
                if "stat" in self._memo:
                    del self._memo["stat"]
            return self
        else:
            return disambiguate(self, must_exist)
    return call


SCons.Node.FS.Entry.disambiguate = _wrap_SCons_Node_FS_Entry_disambiguate(SCons.Node.FS.Entry.disambiguate)
# have to add File node object as well as the "class" definition
# does not get updated with the base class modification (monkey patch)
SCons.Node.FS.File.disambiguate = _wrap_SCons_Node_FS_Entry_disambiguate(SCons.Node.FS.File.disambiguate)


def _source_scanner():
    '''
    Creates a scanner object to be used for C{FileSymbolicLink} nodes  dependences resolution.
    The scanner object is intended to be used primarily by C{CCopy} builder.
    '''

    def find_closest_linkto(node, targets):
        node_abspath = node.abspath

        return max(targets, key=lambda x: len(os.path.commonprefix([node_abspath, x.abspath])))

    def function(node, env, path=()):
        '''
        Scanner main function.

        @param node: A node object to be scanned.
        @param env: C{SCons.Script.Environment} instance.
        @param path: SCons documentation says: "The path argument is a tuple (or list) of directories that can be searched for files."
        But don't be confused. We create the tuple using C{path_function} and in our case it either is empty or
        contains one FileSymbolicLink node - the target.
        '''

        if len(path) != 1:
            return []

        source = path[0]
        target = node

        if not isinstance(source, FileSymbolicLink):
            # This source is not a symlink. So nothing needs to be done
            return []
        elif not isinstance(target, FileSymbolicLink):
            # if the source is a symlink and the target is a file
            # the target really is a symlink to the "source". Elavate the target
            ensure_node_is_symlink(target)

        linkto = source.linkto
        if linkto:
            # if the target has a linkto property set use it.
            result = target.Entry(linkto)
            return [result] if not result in target.children(scan=0) else []
        '''
        #double check this case...
        if isinstance(node, FileSymbolicLink) and node.linkto:
            try:
                # A node pointed by source node's linkto may be copied into several
                # locations. Use find_closest_linkto function to find a node which is
                # the closest one to 'target'. The best match would be a file located
                # in the same dir as the FileSymbolicLink to be created.
                result = find_closest_linkto(target,
                                             node.Entry(node.linkto).attributes.copiedas)
                target.linkto = target.rel_path(result)
                return [result] if not result in target.children(scan=0) else []
            except (AttributeError, IndexError):
                pass
        '''
        return []

    def path_function(env, scons_dir, target, source, arg=None):
        '''
        Scanner path_function. We don't make a real path_function here we use
        it as the way to pass target into Scanner function.
        '''
        return tuple(node for node in source if isinstance(node.disambiguate(), FileSymbolicLink))

    return Scanner(function, path_function=path_function, name="symlink-scanner")


symlink_scanner = _source_scanner()


def SymLinkEnv(env, name, linkto, **kw):
    """
    C{linkto} may be either string, a node, or None. If it is None the function will just return
    a SymLink node. The node must exists of must be built with builder other then env.SymLink.
    If C{linkto} is a node it will be treated as C{source} and the target node
    will depend on it. If it is a string the code will create 'dangling' link.
    """
    target = SCons.Util.flatten(name)
    if len(target) != 1:
        raise SCons.Errors.UserError('SymLink can operate only on a single target but not on {0}'.format(name))

    if not linkto:
        raise SCons.Errors.UserError('Do not know how to handle empty linkto parameter')

    linkto = SCons.Util.flatten(linkto)
    if len(linkto) != 1:
        raise SCons.Errors.UserError("Symlink may point only to a single file, directory or other link")

    linkto = linkto[0]
    if isinstance(linkto, SCons.Node.FS.Base):
        source = [linkto]
        linkto = None
    else:
        source = []

    tmp = env.__make_link__(target=target, source=source, linkto=linkto, **kw)
    if len(tmp) > 1:
        raise SCons.Errors.UserError("Symlink can only have one Target")
    return tmp


def make_link_Emit(target, source, env):
    """
    If the C{source} list is empty create 'dangling' or 'broken' link
    based on C{linkto} environment value. The function will not generate
    a C{source} list in this case.
    """
    assert len(target) == 1
    target = ensure_node_is_symlink(target[0])
    linkto = env.get('linkto')
    if source:
        assert linkto is None and len(source) == 1
        target.linkto = target.rel_path(source[0])
    else:
        assert linkto
        target.linkto = str(linkto)

    return ([target], source)


def make_link_bf(target, source, env):
    assert len(target) == 1
    target = target[0]
    api.output.print_msg("Creating SymLink {0} pointing to {1}".format(target.path, target.linkto))
    try:
        os_symlink(target.linkto, target.abspath, False)
    except OSError:
        # 2nd try. If the exception's reason is other than 'File Exists' it will be raised again.
        os.unlink(target.abspath)
        os_symlink(target.linkto, target.abspath, False)

    return None


api.register.add_builder('__make_link__', SCons.Builder.Builder(
    action=SCons.Action.Action(make_link_bf, cmdstr="Symbolic link $TARGET -> ${TARGET.linkto}"),
    target_factory=SCons.Node.FS.FileSymbolicLink,
    source_factory=SCons.Node.FS.Entry,
    single_source=1,
    emitter=make_link_Emit,
    target_scanner=symlink_scanner
))


def ResolveSymLinkChain(env, link):
    """
    Function is used to determine files "hidden" by a symbolic link.
    Assume we have a chain A->B->C->D. Passing A as the function parameter
    will make the function return a list consisting of A, B, C, and D nodes.

    @param env: C{SCons.Script.Environment} instance
    @param link: C{string}, C{list}, or a C{node} beginning the chain(s).
    """
    result = []
    tmp = SCons.Util.flatten(link)

    while tmp:
        node = env.Entry(tmp.pop(0))
        result.append(node)

        node.disambiguate()
        if isinstance(node, FileSymbolicLink):
            linkto = node.Entry(node.linkto)
            tmp.append(linkto)
            if node.name == linkto.name:
                # if file name part of a link and its target are the same
                # use the 'real' file instead of link
                result[-1] = linkto

    return result


SConsEnvironment.SymLink = SymLinkEnv
SConsEnvironment.ResolveSymLinkChain = ResolveSymLinkChain

# vim: set et ts=4 sw=4 ai ft=python :
