#pylint: disable=missing-docstring

import sys
import os
import shutil
import stat
import errno
from collections import deque, namedtuple

import SCons.Script
from SCons.Script.SConscript import SConsEnvironment

import parts.common as common
import parts.core.util as util
import parts.api as api
import parts.overrides.symlinks as symlinks
import parts.pattern as pattern

class CCopyException(Exception):
    def __init__(self, exc):
        Exception.__init__(self)
        self.exc = exc

CopyBuilderDescription = namedtuple('CopyBuilderDescription',
                                    'builderName ccopyName copyFunctions')

if sys.platform == 'win32':
    import msvcrt
    import ctypes
    from ctypes.wintypes import BOOLEAN, LPWSTR, DWORD, BOOL, FILETIME, HANDLE

    # taken from MSDN
    ERROR_INVALID_FUNCTION = 1
    ERROR_SHARING_VIOLATION = 32

    def describeWinFunc(name, argtypes=None):
        def stubFunction(*_):
            ctypes.set_last_error(ERROR_INVALID_FUNCTION)
            return 0
        try:
            func = getattr(ctypes.windll.kernel32, name)
        except AttributeError:
            return stubFunction
        # this function is return value is messed up because of a programmer mistake as MS
        # have to reprototype it do it works correctly. basically make return a BOOLEAN
        func.argtypes = argtypes or (LPWSTR, LPWSTR, DWORD)
        func.restype = BOOLEAN
        return func

    CreateSymbolicLink = describeWinFunc('CreateSymbolicLinkW')
    CreateHardLink = describeWinFunc('CreateHardLinkW')
    CopyFile = describeWinFunc('CopyFileW', (LPWSTR, LPWSTR, BOOL))

    class ByHandleFileInformation(ctypes.Structure):
        _fields_ = [('dwFileAttributes', DWORD),
                    ('ftCreationTime', FILETIME),
                    ('ftLastAccessTime', FILETIME),
                    ('ftLastWriteTime', FILETIME),
                    ('dwVolumeSerialNumber', DWORD),
                    ('nFileSizeHigh', DWORD),
                    ('nFileSizeLow', DWORD),
                    ('nNumberOfLinks', DWORD),
                    ('nFileIndexHigh', DWORD),
                    ('nFileIndexLow', DWORD)]

    GetFileInformationByHandle = ctypes.windll.kernel32.GetFileInformationByHandle
    GetFileInformationByHandle.argtypes = (HANDLE, ctypes.POINTER(ByHandleFileInformation))
    GetFileInformationByHandle.restype = BOOL

    FileIdentifiers = namedtuple('FileIdentifiers', 'volume indexHigh indexLow')

    def _areFilesHardlinked(*names):
        '''
        On Windows hardlinks to a single file entry all share the same set of identifiers, that
        is: volume serial number and file index in NTFS master file table; so to check if some
        files are actually hardlinks to the same contents we compute the set of those
        identifiers and then check this set length; if it's equal to 1 it means all files have
        equal identifiers => they're hardlinked.
        '''
        identifiers = set()
        for name in names:
            try:
                with open(name, 'r') as targetFile:
                    handle = msvcrt.get_osfhandle(targetFile.fileno())
                    fileInfo = ByHandleFileInformation()
                    if GetFileInformationByHandle(handle, fileInfo):
                        identifiers.add(FileIdentifiers(volume=fileInfo.dwVolumeSerialNumber,
                                                        indexHigh=fileInfo.nFileIndexHigh,
                                                        indexLow=fileInfo.nFileIndexLow))
                    else:
                        raise ctypes.WinError()
            except (OSError, IOError) as exc:
                if exc.errno == errno.ENOENT:
                    # if any of names doesn't exist we say they aren't hardlinks of one another
                    return False
                raise
        return len(identifiers) == 1

    def _reportError(message, dest):
        lastError = ctypes.GetLastError()
        errorMessage = ctypes.FormatError(lastError)
        # convert Windows error code to errno using Python's implementation of WindowsError
        lastErrno = WindowsError(lastError, '').errno
        api.output.verbose_msgf("ccopy", "{0}: {1}", message, errorMessage)
        raise CCopyException(IOError(lastErrno, errorMessage, unicode(dest)))

    def copy_hard(dest, source):
        if not CreateHardLink(unicode(dest), unicode(source), 0):
            _reportError("Failed to create HardLink", dest)

    def copy_soft(dest, source):
        dirName, baseName = os.path.split(source)
        relativeSource = os.path.join(common.relpath(dirName, os.path.dirname(dest)), baseName)
        if not CreateSymbolicLink(unicode(dest), unicode(relativeSource), 0):
            _reportError("Failed to create SymLink", dest)

    def copy_copy(dest, source):
        if not CopyFile(unicode(source), unicode(dest), False):
            _reportError("Failed to copy", dest)

else:
    FileIdentifiers = namedtuple('FileIdentifiers', 'device inode')
    def _areFilesHardlinked(*names):
        '''
        On POSIX hardlinks to the same file entry all share the same identifiers, that is:
        device id (on which files are located... cross-device hardlinks are forbidden) and
        inode number (effectively it's the same as on Windows).
        The logic for checking is the same as for Windows case, see above.
        '''
        identifiers = set()
        for name in names:
            try:
                statInfo = os.lstat(name)
                identifiers.add(FileIdentifiers(device=statInfo.st_dev, inode=statInfo.st_ino))
            except (OSError, IOError) as exc:
                if exc.errno == errno.ENOENT:
                    # if any of names doesn't exist we say they aren't hardlinks of one another
                    return False
                raise
        return len(identifiers) == 1

    def _reportError(exception, message, dest):
        api.output.verbose_msgf("ccopy", "{0}: {1}", message, exception)
        # we create an exception which has the same values as came from outside but we also
        # add filename which caused the original exception
        raise CCopyException(type(exception)(exception.errno, exception.strerror, dest))

    def copy_hard(dest, source):
        try:
            os.link(source, dest)
        except (OSError, IOError) as ex:
            _reportError(ex, "Failed to create HardLink", dest)

    def copy_soft(dest, source):
        try:
            os.symlink(source, dest)
        except (OSError, IOError) as ex:
            _reportError(ex, "Failed to create SymLink", dest)

    def copy_copy(dest, source):
        try:
            shutil.copy2(source, dest)
            # copy source permissions and add owner write permission
            mode = os.stat(source)
            os.chmod(dest, stat.S_IMODE(mode[stat.ST_MODE]) | stat.S_IWRITE)
        except (OSError, IOError) as ex:
            _reportError(ex, "Failed to copy", dest)

def clear_dest(dest):
    if os.path.exists(dest):
        api.output.verbose_msgf("ccopy",
                'File: {0} exists on disk, deleting file so links can be created correctly',
                dest)
        os.remove(dest)

try:
    WindowsError
except NameError:
    WindowsError = None

def copytree(src, dst):
    '''
    We use our version of copytree because one from shutil fails when destination
    directory already exists.
    '''
    dirs = deque(['.'])
    while dirs:
        current = dirs.popleft()
        src_dir = os.sep.join((src, current))
        dst_dir = os.sep.join((dst, current))

        # Make sure the destination directory exists
        try:
            os.makedirs(dst_dir)
        except OSError, error:
            if error.errno == errno.EEXIST:
                if not os.path.isdir(dst_dir):
                    raise SCons.Errors.UserError("cannot overwrite non-directory "
                            "'%s' with a directory '%s'" % (dst_dir, src_dir))
            else:
                raise

        # Iterate by source directory entries.
        # Files are copied, directories are add to the dirs list.
        for entry in os.listdir(src_dir):
            src_entry = os.sep.join((src_dir, entry))
            if os.path.isdir(src_entry):
                dirs.append(os.sep.join((current, entry)))
            else:
                shutil.copy2(src_entry, os.sep.join((dst_dir, entry)))

        try:
            shutil.copystat(src, dst)
        except OSError, why:
            if WindowsError and isinstance(why, WindowsError):
                # Copying file access times may fail on Windows
                pass
            else:
                raise

def CCopyFuncWrapper(env, dest, source, copyfunc=None):
    if os.path.isdir(source):
        copytree(source, dest)
    else:
        (copyfunc or copy_copy)(dest, source)

def CCopyStringFunc(target, source, env):
    target = str(target[0])
    if not source[0].exists():
       source = [source[0].srcnode()]
    source = str(source[0])
    targetType = 'directory' if os.path.isdir(source) else 'file'
    targetDir, targetBasename = os.path.split(target)
    return 'Parts: Copying %s: "%s" to "%s" as: "%s"' % (targetType, source, targetDir,
                                                         targetBasename)

def CCopyEmit(target, source, env):
    target, source = target[0], source[0]
    target.must_be_same(type(source))
    return [target], [source]

class CCopy(object):
    default = 0
    copy = 1
    hard_soft_copy = 2
    soft_hard_copy = 3
    hard_copy = 4
    soft_copy = 5

    DEFAULT_NAME = 'hard-soft-copy'

    @classmethod
    def convert(cls, logicName):
        if util.isString(logicName):
            result = getattr(cls, logicName.replace('-', '_'), None)
            if isinstance(result, int):
                return result
            api.output.warning_msgf("unknown string value for CCOPY_LOGIC: {0}", logicName)
        return logicName

    @classmethod
    def getList(cls):
        return [attrName.replace('_', '-') for (attrName, attrValue) in cls.__dict__.iteritems()
                if isinstance(attrValue, int)]

    @classmethod
    def getCopyBuilder(cls, env, copyLogic):
        if copyLogic == cls.default:
            # fallback to the safest copy logic
            copyLogic = cls.convert(env.get('CCOPY_LOGIC', cls.copy))
        else:
            copyLogic = cls.convert(copyLogic)
        try:
            description = COPY_BUILDERS[copyLogic]
        except KeyError:
            description = COPY_BUILDERS[cls.copy]
        return getattr(env, description.builderName)

def CCopyWrapper(env, target=None, source=None, copy_logic=CCopy.default, **kw):
    target_factory = env.fs
    # test args a little
    try:
        dnodes = env.arg2nodes(target, target_factory.Dir)
    except TypeError:
        trace_back = sys.exc_info()[-1]
        # now try to get the bad guy by going to the end:
        try:
            while trace_back.tb_next:
                trace_back = trace_back.tb_next
            try:
                bad_value = str(trace_back.tb_frame.f_locals['self'])
            except KeyError:
                bad_value = 'Unknown'
            api.output.error_msg(("Target `%s' is a file, but should be a directory. "
                                  "Perhaps you have the arguments backwards?") % bad_value)
        finally:
            del trace_back

    copyBuilder = CCopy.getCopyBuilder(env, copy_logic)
    sources = common.make_list(source)
    n_targets = []

    for dnode in dnodes:
        for src in sources:
            if util.isString(src):
                src = env.arg2nodes(src, env.fs.Entry)[0]
                # Prepend './' so the lookup doesn't interpret an initial
                # '#' on the file name portion as meaning the Node should
                # be relative to the top-level SConstruct directory.
                e = dnode.Entry(os.sep.join(['.', src.name]))
            elif  isinstance(src, pattern.Pattern):
                # this case needs some tweaking to deal with symlinks
                t, sr = src.target_source(dnode.abspath)                
                n_targets.extend(env.CCopyAs(target=t, source=sr))
                continue
            elif isinstance(src, SCons.Node.FS.Dir):
                e = dnode.Dir(os.sep.join(['.', src.name]))
            elif isinstance(src, symlinks.FileSymbolicLink):
                #symlinks.ensure_node_is_symlink(e)
                try:
                    e = dnode.FileSymbolicLink(os.sep.join(['.', src.name]))
                except:
                    # this is a hack to deal with some backward compatibility issue
                    # with deal with symlinks in old code
                    e = dnode.Entry(os.sep.join(['.', src.name]))
                    symlinks.ensure_node_is_symlink(e)
            elif isinstance(src, SCons.Node.FS.File):
                e = dnode.File(os.sep.join(['.', src.name]))
            else:
                # should not happen...
                e = dnode.Entry(os.sep.join(['.', src.name]))

            # Let source node know what copies of it are to be created.
            # This information will be used to set up correct symbolic
            # links in the destination directory
            try:
                copiedas = src.attributes.copiedas
            except AttributeError:
                src.attributes.copiedas = copiedas = []
            copiedas.append(e)

            copyTargets = copyBuilder(target=e, source=src, **kw)
            try:
                copyTargets[0].attributes = src.attributes
            except (AttributeError, IndexError):
                pass
            n_targets.extend(copyTargets)

    #for target in n_targets:
    #    target.set_precious(True)
    return n_targets

def CCopyAsWrapper(env, target=None, source=None, copy_logic=CCopy.default, **kw):
    result = []
    copyBuilder = CCopy.getCopyBuilder(env, copy_logic)
    source = env.arg2nodes(source)
    target = common.make_list(target)
    if len(target) != len(source):
        api.output.error_msg("Number of targets and sources should be the same")

    for src, tgt in zip(source, target):
        # if the target is a string and the source is a symlink,
        # we want to make the target a symlink as well
        if util.isString(tgt) and isinstance(src, symlinks.FileSymbolicLink):
            targetDirName, targetFileName = os.path.split(tgt)
            tgt = env.Dir(targetDirName).FileSymbolicLink(os.sep.join(('.', targetFileName)))
            try:
                copiedas = src.attributes.copiedas
            except AttributeError:
                src.attributes.copiedas = copiedas = []
            copiedas.append(tgt)
        result.extend(copyBuilder(tgt, src, **kw))

    for target in result:
        target.set_precious(True)

    return result

def CCopyFunc(target, source, env, copy_logic):
    # get the logger for the given part
    output = env._get_part_log_mapper()
    # tell it we are starting a task
    taskId = output.TaskStart(CCopyStringFunc(target, source, env) + "\n")

    assert len(target) == len(source), "\ntarget: %s\nsource: %s" % (map(str, target),
                                                                    map(str, source))

    for targetEntry, sourceEntry in zip(target, source):
        #Get info if this should be handled as a symlink
        if isinstance(sourceEntry, symlinks.FileSymbolicLink):
            assert sourceEntry.exists() and sourceEntry.linkto
            # A symbolic link can only be a copy of another symlink.
            # Convert a target node to FileSymbolicLink this is needed for
            # correct up-to-date checks during incremental builds
            symlinks.ensure_node_is_symlink(targetEntry)
            if targetEntry.linkto is None:
                targetEntry.linkto = sourceEntry.linkto
            symlinks.make_link_bf([targetEntry], [targetEntry.Entry(targetEntry.linkto)], env)
        else:
            # there is a small issue in that variant directory and behave differently from
            # the File variant case. The main differnce is that the default points the variant
            # while the file case points to the source. This check makes sure we get the correct one
            if not sourceEntry.exists():
                sourceEntry = sourceEntry.srcnode()            

            #Do normal copy stuff
            CCopyFuncWrapper(env, targetEntry.get_path(), sourceEntry.get_path(), copy_logic)
    #tell logger the task has end correctly.
    output.TaskEnd(taskId, 0)
    return

def generateCopyBuilder(description):
    '''
    This function produces *functions* to be used as SCons Builder actions; note that value of
    "description" parameter is bound to the functions this generator produced (see function
    closure in Python).
    '''
    def doCopy(dest, source):
        '''
        The logic for copying function is simple - try all the copyFunctions bound to this
        instance of the function (each SCons builder generated by generateCopyBuilder() has its
        own unique instance of doCopy() with "description" bound by closure thing).
        If all functions failed try simple copying.
        '''
        if len(dest) >= 200 and not dest.startswith("\\\\?\\") and sys.platform == 'win32':
            dest = unicode("\\\\?\\" + os.path.abspath(dest))
        if len(source) >= 200 and not source.startswith("\\\\?\\") and sys.platform == 'win32':
            source = unicode("\\\\?\\" + os.path.abspath(source))
        if copy_hard in description.copyFunctions and not os.path.isdir(dest):
            # Check if dest is a hardlink of source - to save time; also on
            # Windows hardlinks have a quirk - if a file is opened without
            # SHARED_DELETE via some hardlink it's impossible to delete _any_
            # hardlink.  So we're just checking if the file we're trying to
            # remove prior copying is actually a hardlink to the one we're
            # trying to create, and if so we just stop the copy process
            if _areFilesHardlinked(source, dest):
                api.output.verbose_msgf("ccopy", "{0}: {1} and {2} are hardlinked, " + \
                                                 "no copying needed",
                                        description.ccopyName, dest, source)
                return

        api.output.verbose_msgf("ccopy", "{0}: dest={1} source={2}", description.ccopyName,
                                dest, source)
        clear_dest(dest)
        for copyFunc in description.copyFunctions:
            try:
                return copyFunc(dest, source)
            except CCopyException:
                pass
        try:
            return copy_copy(dest, source)
        except CCopyException as err:
            raise err.exc
    def doAction(target, source, env):     
        return CCopyFunc(target, source, env, doCopy)

    api.register.add_builder(description.builderName,
            SCons.Builder.Builder(action=SCons.Action.Action(doAction, CCopyStringFunc),
                                  target_factory=SCons.Node.FS.Entry,
                                  source_factory=SCons.Node.FS.Entry,
                                  emitter=CCopyEmit, source_scanner=symlinks.source_scanner,
                                  name='CCOPY'))

COPY_BUILDERS = {
    CCopy.hard_soft_copy: CopyBuilderDescription(builderName='__CCopyBuilderHSC__',
                                                 ccopyName='copy_hard_soft',
                                                 copyFunctions=(copy_hard, copy_soft)),
    CCopy.soft_hard_copy: CopyBuilderDescription(builderName='__CCopyBuilderSHC__',
                                                 ccopyName='copy_soft_hard',
                                                 copyFunctions=(copy_soft, copy_hard)),
    CCopy.hard_copy: CopyBuilderDescription(builderName='__CCopyBuilderHC__',
                                            ccopyName='copy_hard',
                                            copyFunctions=(copy_hard,)),
    CCopy.soft_copy: CopyBuilderDescription(builderName='__CCopyBuilderSC__',
                                            ccopyName='copy_soft',
                                            copyFunctions=(copy_soft,)),
    CCopy.copy: CopyBuilderDescription(builderName='__CCopyBuilderC__', ccopyName='copy',
                                       copyFunctions=()),
}

# This is what we want to be setup in parts
SConsEnvironment.CCopy = CCopyWrapper
SConsEnvironment.CCopyAs = CCopyAsWrapper
SConsEnvironment.CCopyFuncWrapper = CCopyFuncWrapper

for builderDescription in COPY_BUILDERS.itervalues():
    generateCopyBuilder(builderDescription)

api.register.add_global_object('CCopy', CCopy)
api.register.add_global_parts_object('CCopy', CCopy)
api.register.add_enum_variable('CCOPY_LOGIC', CCopy.DEFAULT_NAME, '', CCopy.getList())
