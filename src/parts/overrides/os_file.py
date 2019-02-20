# this file provdies overides to allow windows ( or any tweaks need for other systems) to work with hard and soft links.
# Given that the Python uses C file handling and for historical reason MS has not updated this API to correctly
# open file in a shared moded as windows wants it, but instead a locked mode, the api calls to hard links and symlink
# tend to fail with call to delete or rename on windows. A simple ( well not so simple) to call win32 API's corrects this problem
from __future__ import absolute_import, division, print_function

import ctypes
import os
import sys

from SCons.Script import _SConscript

if sys.platform == 'win32':
    import ctypes.wintypes
    # This allow us to up file in a non-exclusive mode

    import builtins
    import msvcrt

    try:
        _original_file = builtins.file
    except BaseException:
        pass
    _original_open = builtins.open

    # this import to stop SCons from doing what it is doing with open/file
    import SCons.Platform.win32  # pylint: disable=unused-import

    # mappings of common win32 flags
    FILE_SHARE_READ = 1
    FILE_SHARE_WRITE = 2
    FILE_SHARE_DELETE = 4

    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000

    CREATE_NEW = 1
    CREATE_ALWAYS = 2
    OPEN_EXISTING = 3
    OPEN_ALWAYS = 4
    TRUNCATE_EXISTING = 5

    # the basic ones needed here .. add extra if needed
    FILE_ATTRIBUTE_NORMAL = 0x00000080
    FILE_ATTRIBUTE_TEMPORARY = 0x00000100
    FILE_FLAG_DELETE_ON_CLOSE = 0x04000000

    GetFullPathNameW = ctypes.windll.kernel32.GetFullPathNameW
    GetFullPathNameW.argtypes = (ctypes.c_wchar_p,
                                 ctypes.wintypes.DWORD,
                                 ctypes.c_wchar_p,
                                 ctypes.c_void_p)
    GetFullPathNameW.restype = ctypes.wintypes.DWORD

    CreateFileW = ctypes.windll.kernel32.CreateFileW
    CreateFileW.argtypes = (ctypes.c_wchar_p,  # lpFileName
                            ctypes.c_uint32,  # dwDesiredAccess
                            ctypes.c_uint32,  # dwSharedMode
                            ctypes.c_void_p,  # lpSecurityAttributes
                            ctypes.c_uint32,  # dwCreationDisposition
                            ctypes.c_uint32,  # dwFlagsAndAttributes
                            ctypes.c_void_p,  # hTemplateFile
                            )
    CreateFileW.restype = ctypes.c_long

    DeleteFileW = ctypes.windll.kernel32.DeleteFileW
    DeleteFileW.argtypes = (ctypes.c_wchar_p,)
    DeleteFileW.restype = ctypes.wintypes.BOOL

    if sys.version_info >= (3, 0):
        # the new python3 allows for a much better way to create the files

        def map_basic_create(mode):
            mode = mode & (os.O_CREAT | os.O_EXCL | os.O_TRUNC)
            if mode == os.O_EXCL:
                return OPEN_EXISTING
            if mode == os.O_CREAT:
                return OPEN_ALWAYS
            if mode == (os.O_CREAT | os.O_EXCL | os.O_TRUNC) or mode == (os.O_CREAT | os.O_EXCL):
                return CREATE_NEW
            if mode == os.O_TRUNC or mode == (os.O_EXCL | os.O_TRUNC):
                return TRUNCATE_EXISTING
            if mode == (os.O_CREAT | os.O_TRUNC):
                return CREATE_ALWAYS

        def map_basic_access(mode):
            mode = mode & (os.O_RDONLY | os.O_WRONLY | os.O_RDWR)
            if mode == os.O_RDONLY:
                return GENERIC_READ
            # not sure if we have an issue here yet ...
            # I am unclear at the moment on encoding.. would this need read in case
            # of append? Ideally this part of of values are handled by python before
            # we get the mode values to set of windows
            if mode == os.O_WRONLY:
                return GENERIC_WRITE
            if mode == os.O_RDWR:
                return GENERIC_READ | GENERIC_WRITE

        def map_mode_to_win32_mode(mode):
            flags = 0
            access = map_basic_access(mode)
            # might be more aggressive than needed...
            shared = FILE_SHARE_DELETE | FILE_SHARE_READ | FILE_SHARE_WRITE
            create = map_basic_create(mode)
            attributes = FILE_ATTRIBUTE_NORMAL
            # might not need this case....
            if mode & os.O_TEMPORARY:
                flags |= FILE_FLAG_DELETE_ON_CLOSE
                access |= DELETE
            # might not need this case....
            if mode & os.O_SHORT_LIVED:
                attributes |= FILE_ATTRIBUTE_TEMPORARY

            return (flags, access, shared, create, attributes)

        def shared_open(filename, intmode):
            # make this and abspath to help deal with long path names
            if len(filename) > 16 and not filename.startswith("\\\\"):
                filename = str("\\\\?\\" + os.path.abspath(filename))
            else:
                filename = str(filename)

            flags, access, shared = map_mode_to_win32_mode(intmode)
            handle = CreateFileW(
                filename,  # the file
                access,  # read, write modes
                shared,  # add share delete
                None,  # default security
                create,  # If we create the file or not
                flags | attributes,  # normal attribute..  FILE_ATTRIBUTE_NORMAL
                0  # no Template
            )
            if handle == -1:
                # we have some error, return it in a python compatible way
                raise IOError(ctypes.GetLastError(), ctypes.FormatError(ctypes.GetLastError()),
                              filename)

            fd = msvcrt.open_osfhandle(handle, intmode)
            return fd

            def open_wrapper(*lst, **kw):
                # don't want to worry about changes to the open function.. so just pass generic args
                # the only case we worry about is if they pass there own opener ( should be *VERY* rare)
                # but just in case we will check and use theres if it exists
                if "opener" in kw and kw["opener"] is not None:
                    return _original_open(*lst, **kw)
                return _original_open(*lst, opener=shared_open, **kw)

            builtins.open = shared_open
            # modify handle in SCons
            _SConscript.open = _original_open

    else:
        # for older python 2.7
        def get_win32_desired_access(mode):
            ret = 0
            if 'r' in mode:
                ret = GENERIC_READ
            if 'w' in mode or '+' in mode or 'a' in mode:
                ret |= GENERIC_WRITE
            return ret

        def get_win32_shared_mode(mode):
            ret = FILE_SHARE_DELETE | FILE_SHARE_READ | FILE_SHARE_WRITE
            # if mode.find('w')!=-1 or mode.find('+')!=-1 or mode.find('a')!=-1:
            #    ret=ret|FILE_SHARE_WRITE
            return ret

        def get_win32_creation_disposition(mode):
            if 'w' in mode:
                return CREATE_ALWAYS
            elif 'r' in mode:
                return OPEN_EXISTING
            else:
                return OPEN_ALWAYS

        def shared_open(filename, mode='r', bufsize=-1):
            # this is sort of ugly
            # open the file with better shared flags

            if not (set(['a', 'w', 'r']) & set(mode)):
                mode = 'r' + mode
            # make this and abspath to help deal with long path names
            if len(filename) > 16 and not filename.startswith("\\\\"):
                filename = str("\\\\?\\" + os.path.abspath(filename))
            else:
                filename = str(filename)
            desired_access = get_win32_desired_access(mode)
            shared_mode = get_win32_shared_mode(mode)
            creation_disposition = get_win32_creation_disposition(mode)
            handle = CreateFileW(filename,  # the file
                                 desired_access,  # read, write modes
                                 shared_mode,  # add share delete
                                 None,  # default security
                                 creation_disposition,  # If we create the file or not
                                 FILE_ATTRIBUTE_TEMPORARY,  # normal attribute..  FILE_ATTRIBUTE_NORMAL
                                 0  # no Template
                                 )
            if handle == -1:
                # we have some error, return it in a python compatible way
                raise IOError(ctypes.GetLastError(), ctypes.FormatError(ctypes.GetLastError()),
                              filename)

            # not sure if I should modify flags passed here,
            # as the next call will get them
            # but it does not seem to hurt
            # maps native handle to a C handle
            if 'b' in mode:
                fd = msvcrt.open_osfhandle(handle, os.O_BINARY)
            else:
                fd = msvcrt.open_osfhandle(handle, os.O_TEXT)
            # map the C handle to a python handle
            f = os.fdopen(fd, mode, bufsize)
            if 'a' in mode:
                f.seek(0, os.SEEK_END)
            return f

            # replace the built in values with the new values
            builtins.file = shared_open
            builtins.open = shared_open
            # modify handle in SCons
            _SConscript.open = _original_open
            _SConscript.file = _original_file

    # at this level these call replace the os.<file calls> that may be called
    # by the user
    # as for some reason some of these call lock the files in the python imple
    # ideally this should be done with a reimpl of SCons.Node.FS.LocalFS as
    # all uses will use
    # the File or Dir nodes to do all file operation in SCon someday
    # this will then change to allow help in that migration

    def win32_rm(path):
        if len(path) >= 200 and not path.startswith("\\\\?\\"):
            path = str("\\\\?\\" + os.path.abspath(path))
        else:
            path = str(path)
        if not DeleteFileW(path):
            raise WindowsError(ctypes.GetLastError(), ctypes.FormatError(ctypes.GetLastError()),
                               path)

    os.remove = win32_rm
    os.unlink = win32_rm

    _orginal_listdir = os.listdir

    def listdir(dir):
        if len(dir) >= 200 and not dir.startswith("\\\\?\\"):
            dir = str("\\\\?\\" + os.path.abspath(dir))
        return _orginal_listdir(dir)
    os.listdir = listdir

    _orginal_stat = os.stat

    def stat(dir):
        if len(dir) >= 200 and not dir.startswith("\\\\?\\"):
            dir = str("\\\\?\\" + os.path.abspath(dir))
        return _orginal_stat(dir)
    os.stat = stat

    _orginal_mkdir = os.mkdir

    def mkdir(dir, mode=0o777):
        if len(dir) >= 200 and not dir.startswith("\\\\?\\"):
            dir = str("\\\\?\\" + os.path.abspath(dir))
        return _orginal_mkdir(dir, mode)
    os.mkdir = mkdir

    def abspath(dir):
        buf = ctypes.create_unicode_buffer(1024)
        ret = GetFullPathNameW(dir, 1024, buf, 0)
        if ret > 1024:
            buf = ctypes.create_unicode_buffer(ret)
            ret = GetFullPathNameW(dir, 1024, buf, 0)
        if ret == 0:
            # we have an error
            raise WindowsError(ctypes.GetLastError(), ctypes.FormatError(ctypes.GetLastError()), dir)
        return buf.value
    os.path.abspath = abspath


# vim: set et ts=4 sw=4 ai :
