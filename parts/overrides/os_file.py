# this file provdies overides to allow windows ( or any tweaks need for other systems) to work with hard and soft links.
# Given that the Python uses C file handling and for historical reason MS has not updated this API to correctly
# open file in a shared moded as windows wants it, but instead a locked mode, the api calls to hard links and symlink
# tend to fail with call to delete or rename on windows. A simple ( well not so simple) to call win32 API's corrects this problem

import os
import sys
import ctypes

from SCons.Script import _SConscript

if sys.platform == 'win32':
    import ctypes.wintypes
    #This allow us to up file in a non-exclusive mode

    import __builtin__
    import msvcrt

    _original_file = __builtin__.file
    _original_open = __builtin__.open

    # this import to stop SCons from doing what it is doing with open/file
    import SCons.Platform.win32 #pylint: disable=unused-import

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

    def get_win32_desired_access(mode):
        ret = 0
        if 'r' in mode:
            ret = GENERIC_READ
        if 'w' in mode or '+' in mode or 'a' in mode:
            ret |= GENERIC_WRITE
        return ret

    def get_win32_shared_mode(mode):
        ret = FILE_SHARE_DELETE | FILE_SHARE_READ | FILE_SHARE_WRITE
        #if mode.find('w')!=-1 or mode.find('+')!=-1 or mode.find('a')!=-1:
        #    ret=ret|FILE_SHARE_WRITE
        return ret

    def get_win32_creation_disposition(mode):
        if 'w' in mode:
            return CREATE_ALWAYS
        elif 'r' in mode:
            return OPEN_EXISTING
        else:
            return OPEN_ALWAYS

    GetFullPathNameW = ctypes.windll.kernel32.GetFullPathNameW
    GetFullPathNameW.argtypes = (ctypes.c_wchar_p,
           ctypes.wintypes.DWORD,
           ctypes.c_wchar_p,
           ctypes.c_void_p)
    GetFullPathNameW.restype = ctypes.wintypes.DWORD

    CreateFileW = ctypes.windll.kernel32.CreateFileW
    CreateFileW.argtypes = (ctypes.c_wchar_p, # lpFileName
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

    def shared_open(filename, mode='r', bufsize=-1):
        # this is sort of ugly
        # open the file with better shared flags

        if not (set(['a', 'w', 'r']) & set(mode)):
            mode = 'r' + mode
        #make this and abspath to help deal with long path names
        if len(filename) > 16 and not filename.startswith("\\\\"):
            filename = unicode("\\\\?\\" + os.path.abspath(filename))
        else:
            filename = unicode(filename)        
        desired_access = get_win32_desired_access(mode)
        shared_mode = get_win32_shared_mode(mode)
        creation_disposition = get_win32_creation_disposition(mode)
        handle = CreateFileW(filename, # the file
                    desired_access,# read, write modes
                    shared_mode,# add share delete
                    None, #default securtity
                    creation_disposition, #If we create the file or not
                    128, # normal attribute..  FILE_ATTRIBUTE_NORMAL
                    0 # no Template
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
    __builtin__.file = shared_open
    __builtin__.open = shared_open
    # modify handle in SCons
    _SConscript.open = _original_open
    _SConscript.file = _original_file

    ## at this level these call replace the os.<file calls> that may be called
    ## by the user
    ## as for some reason some of these call lock the files in the python imple
    ## ideally this should be done with a reimpl of SCons.Node.FS.LocalFS as
    ## all uses will use
    ## the File or Dir nodes to do all file operation in SCon someday
    ## this will then change to allow help in that migration
    def win32_rm(path):
        if len(path) >= 200 and not path.startswith("\\\\?\\"):
            path = unicode("\\\\?\\" + os.path.abspath(path))
        else:
            path=unicode(path)
        if not DeleteFileW(path):
            raise WindowsError(ctypes.GetLastError(), ctypes.FormatError(ctypes.GetLastError()),
                          path)

    os.remove = win32_rm
    os.unlink = win32_rm

    _orginal_listdir = os.listdir
    def listdir(dir):
        if len(dir) >= 200 and not dir.startswith("\\\\?\\"):
            dir = unicode("\\\\?\\" + os.path.abspath(dir))
        return _orginal_listdir(dir)
    os.listdir = listdir

    _orginal_stat = os.stat
    def stat(dir):        
        if len(dir) >= 200 and not dir.startswith("\\\\?\\"):
            dir = unicode("\\\\?\\" + os.path.abspath(dir))
        return _orginal_stat(dir)
    os.stat = stat
    
    _orginal_mkdir = os.mkdir
    def mkdir(dir,mode=0777):
        if len(dir) >= 200 and not dir.startswith("\\\\?\\"):
            dir = unicode("\\\\?\\" + os.path.abspath(dir))
        return _orginal_mkdir(dir,mode)
    os.mkdir = mkdir
        
    def abspath(dir):
        buf = ctypes.create_unicode_buffer(1024)
        ret = GetFullPathNameW(dir,1024,buf,0)
        if ret > 1024:
            buf = ctypes.create_unicode_buffer(ret)
            ret = GetFullPathNameW(dir,1024,buf,0)
        if ret == 0:
            # we have an error
            raise WindowsError(ctypes.GetLastError(), ctypes.FormatError(ctypes.GetLastError()),dir)
        return buf.value
    os.path.abspath = abspath


# vim: set et ts=4 sw=4 ai :
