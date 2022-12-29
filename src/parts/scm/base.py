

import os
import re
import stat
import subprocess
import sys
from pathlib import Path
import traceback
from typing import List, Union, Optional, cast

import parts.api as api
import parts.common as common
import parts.datacache as datacache
import parts.part_ref as part_ref
import parts.target_type as target_type
from parts.core import util
from parts.reporter import PartRuntimeError as PartRuntimeError

try:
    import urllib.parse
except ImportError:
    import urllib.parse as urlparse


def normalize_url(url):
    # Combine and normalize the URL
    schema, netloc, path, query, fragment = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((schema, netloc, re.sub(r'/+', '/', path),
                                    query, fragment)).rstrip('/')


def removeall(path):
    '''
    This allow for a simple removeall of data on windows or linux. Python
    in general does not like read-only directory deleting. This allow us to
    remove these files from the test area without issue.
    '''
    def rm_link(p):
        try:
            st = os.lstat(p)
            # should exist in 2.6, does not seem to be on some distros of 2.7??
            os.lchmod(p, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)
        except Exception:
            pass
        os.unlink(p)

    def rm_file(p):
        st = os.stat(p)
        os.chmod(p, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)
        os.remove(p)

    def rm_dir(p):
        removeall(p)  # remove all files in directory first
        st = os.stat(p)
        os.chmod(p, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)
        os.rmdir(p)

    if os.path.isfile(path):
        rm_file(path)
        return

    files = os.listdir(path)

    for x in files:
        fullpath = os.path.join(path, x)
        if os.path.islink(fullpath):
            rm_link(fullpath)
        elif os.path.isfile(fullpath):
            rm_file(fullpath)
        elif os.path.isdir(fullpath):
            rm_dir(fullpath)


class base:
    '''
    Base object for all SCM (Software Control Management) objects

    Contain the base logic for all the scm type objects. All objects should use
    this object as its base. The intent of this logic to support getting of sources
    for building not the checking of sources. Check in, push or other maintainance
    logic should be done outside SCons and Parts.
    '''
    __slots__ = [
        '_repository',
        '_server',
        '_allow_parallel',  # Default value is True
        '_pobj',  # Default value is None
        '_env',  # Default value is None
        '_full_path',
        '_use_cache',
        '__update_src',
        '__is_extern',  # is this an extern "part" pull
    ]

    def __init__(self, repository, server=None, use_cache=None):
        '''Constructor for the scm object
        @param self The object pointer
        @param repository The location under in the server to find get the data files
        @param server The scm server to access. If not provided the full value of the repository value is used
        '''

        self._repository = repository
        self._server = server
        self._allow_parallel = True
        self._pobj = None
        self._env = None
        self._full_path = None
        self._use_cache = use_cache
        self.__update_src: Optional[bool] = None
        self.__is_extern: bool = False

    @property
    def isExtern(self) -> bool:
        return self.__is_extern

    @isExtern.setter
    def isExtern(self, val: bool):
        self.__is_extern = val

    @property
    def canMirror(self) -> bool:
        '''
        Returns True if we can make a mirror locally on disk
        '''
        return False

    @property
    def hasMirror(self) -> bool:
        '''
        Returns true if there is a mirror found
        '''
        return False

    @property
    def MirrorPath(self) -> Path:
        '''
        Returns path object to the mirror
        '''
        raise NotImplementedError

    @property
    def useCache(self) -> bool:
        '''
        Returns true if there is a mirror found
        '''
        if self._use_cache is None:
            return self._env["USE_SCM_CACHE"]
        else:
            return self._use_cache

    @property
    def Server(self) -> str:
        '''returns the value of the server

        Subclasses may add to this logic as they might want to define other values to fall back on if the
        server value if None. For example the SVN object will return the value of $SVN_SERVER if the
        server is not set
        '''
        return self._server

    @property
    def Repository(self) -> str:
        '''returns the value of the server

        Subclasses may add to this logic as they might want to define other values based on custom logic.
        '''
        return self._repository

    @property
    def CheckOutDir(self):
        '''returns the path in which we want to checkout to'''
        if self.isExtern:
            return self._env.Dir('$EXTERN_CHECKOUT_DIR').srcnode()
        return self._env.Dir('$CHECK_OUT_DIR').srcnode()

    @property
    def PartFileName(self):
        '''returns the modifed path of the Parts file based on the check out directory'''
        return self._env.Dir(self.CheckOutDir).File(self._pobj.File)

    @property
    def PartFileExists(self) -> bool:
        return os.path.exists(self.PartFileName.abspath)

    @property
    def CheckOutDirExists(self) -> bool:
        return os.path.exists(self.CheckOutDir.abspath)

    @property
    def FullPath(self) -> str:
        ''' returns the full path'''
        if not self._full_path:
            # Combine and normalize the URL
            self._full_path = normalize_url(
                '/'.join((self.Server.rstrip('\\/'), self.Repository)))
        return self._full_path

    def AllowParallelAction(self):
        # change this latter to get value of
        # some policy/variable value
        return True

    def _setup_(self, partobj):
        ''' This sets up the scm object data for real use
        @param partobj The part object that we will want to reference for certain data items
        '''

        # the set the part object
        self._pobj = partobj
        self._env = partobj.Env

        # set up the server and repository data
        if self._server and not self._server.endswith('/'):
            self._server += '/'
        self._repository = self._repository.lstrip('\\/')
        self.UpdateEnv()

    def UpdateEnv(self):
        '''
        Update the with information about the current SCM object
        '''
        if self.isExtern:
            self._env['SCM_EXTERN'] = common.namespace(
                TYPE='unknown',
                CHECKOUT_DIR=''
            )
        else:
            self._env['SCM'] = common.namespace(
                TYPE='unknown',
                CHECKOUT_DIR=''
            )

    def _has_target_match(self, update_option: Union[bool, List[str]]) -> bool:

        if util.isList(update_option):
            for i in cast(List[str], update_option):
                target = target_type.target_type(i)
                tmp = part_ref.PartRef(target)
                if tmp.hasStoredMatch or tmp.hasMatch:
                    if self._pobj in tmp.StoredMatches or self._pobj in tmp.Matches:
                        return True
                else:
                    # this is a little bit of a hack.. will want to refactor this later
                    if datacache.GetCache("part_map") is None:
                        api.output.warning_msgf(
                            "Skipping the update of {0} because there is no part cache for mapping the value '{0}' to the Part",
                            i,
                            print_once=True,
                            show_stack=False)
                    else:
                        api.output.warning_msgf(
                            "Skipping the update of {0} as it is not a known part to update. Is this a type-o?",
                            i,
                            print_once=True,
                            show_stack=False)

        return False

    def NeedsToUpdateMirror(self) -> bool:
        '''
        Checks is we need to update or create the mirror
        '''
        # check that we can mirror the object and we set
        # the ability for the mirror cache to be used

        if self.canMirror and self.useCache:
            update: Union[bool, List[str]] = self._env.GetOption('update_mirror')            
            # src_update = self._env.GetOption('update')
            # check that we have a cache directory
            if not self.hasMirror:
                # no cache exists so create it
                api.output.verbose_msg(['scm.mirror', 'scm'],
                                       'Mirror does not exist for for part: "{}"'.format(self._pobj.Alias))
                ret = True
            # check that we want to update the miror for this object
            elif self._has_target_match(update):
                api.output.verbose_msg(['scm.mirror', 'scm'],
                                       ' --update-mirror switch matched, update needed for: "{}"'.format(self.MirrorPath))
                ret = True
            elif update == False:
                api.output.verbose_msg(['scm.mirror', 'scm'],
                                       ' --update-mirror switch explicitly turned off')
                ret = False
            elif update == "__auto__" and self.NeedsToUpdate():
                # Do update implicitly if user did not say update mirror and the component needs to be updated
                # because of the use of --scm-update switch. This ensures the mirrors get the update states
                api.output.verbose_msg(['scm.mirror', 'scm'],
                                       ' --update-mirror switch implicitly because component needs to be update needed for: "{}"'.format(self.MirrorPath))

                ret = True
            else:
                api.output.verbose_msg(['scm.mirror', 'scm'],
                                       'Scm object does not require mirror to be updated for part: "{}"'.format(self._pobj.Alias))
                ret = False
        else:
            api.output.verbose_msg(['scm.mirror', 'scm'],
                                   'Scm object {0} does not support mirroring for part: "{1}"'.format(self.__class__, self._pobj.Alias))
            ret = False

        return ret

    def NeedsToUpdate(self):
        '''Tell us if this SCM object believe it need to be updated'''
        if self.__update_src is not None:
            return self.__update_src
        ret_val: bool = False
        update = self._env.GetOption('update')
        api.output.verbose_msg(['scm.update', 'scm'], 'SCM update check for part: "%s"' % self._pobj.Alias)
        # do custom check
        if self.do_update_check():
            api.output.verbose_msg(['scm.update', 'scm'], ' do_update_check (custom checks) requires updating')
            ret_val = True
        elif update == '__auto__':
            # do smart logic stuff
            # get the scm-logic value

            logic_type = self._env.GetOption('scm_logic')
            api.output.verbose_msg(['scm.update', 'scm'], ' doing smart logic of "%s"' % logic_type)
            ret: Optional[bool] = None
            if logic_type == 'exists':
                ret = self.do_exist_logic()
            elif logic_type == 'check':
                ret = self.do_check_logic()
            elif logic_type == 'force':
                ret = self.do_force_logic()
            elif logic_type == 'none':
                ret = None
            mod_msg = f'Local modification detected in "{self.CheckOutDir.abspath}".\n Add --update to force update for merge and potential loss of local changes'
            if ret:
                # get policy for how to handle a positive response
                pol = self._env.GetOption('scm_policy')
                api.output.verbose_msgf(['scm.update', 'scm'], "update policy is '{0}'", pol)
                if pol == 'warning':
                    ret_val = False
                    # report the warning
                    api.output.warning_msg(ret, show_stack=False)
                elif pol == 'error':
                    ret_val = False
                    # report the error
                    api.output.error_msg(ret, show_stack=False)
                elif pol == 'checkout-warning':
                    ret_val = False
                    if self.do_exist_logic():
                        api.output.verbose_msg(['scm.update', 'scm'], ret)
                    else:
                        # report the warning
                        api.output.warning_msg(ret, show_stack=False)
                        api.output.warning_msg(
                            "Add --update to force update for merge and potential loss of local changes", show_stack=True)
                elif pol == 'checkout-error':
                    ret_val = False
                    if self.do_exist_logic():
                        api.output.verbose_msg(['scm.update', 'scm'], ret)
                    else:
                        # report the error
                        api.output.error_msg(ret, show_stack=False, exit=False)
                        api.output.error_msg(
                            "Add --update to force update for merge and potential loss of local changes", show_stack=True)
                elif pol == 'message-update':
                    ret_val = True
                    api.output.print_msg(ret)
                    if self.is_modified() and not self._env['SCM_IGNORE_MODIFIED']:
                        api.output.error_msg(mod_msg, show_stack=False)
                    elif os.path.exists(self.CheckOutDir.abspath):
                        api.output.print_msg(
                            f'No local modification detected in "{self.CheckOutDir.abspath}", updating...')
                elif pol == 'warning-update':
                    ret_val = True
                    api.output.warning_msg(ret, show_stack=False)
                    if self.is_modified() and not self._env['SCM_IGNORE_MODIFIED']:
                        api.output.error_msg(mod_msg, show_stack=False)
                    elif os.path.exists(self.CheckOutDir.abspath):
                        api.output.warning_msg(f'No local modification detected in "{self.CheckOutDir.abspath}", updating...', show_stack=False)
                elif pol == 'update':
                    ret_val = True
                    api.output.verbose_msg(['scm.update', 'scm'], ret)
                    if self.is_modified() and not self._env['SCM_IGNORE_MODIFIED']:
                        api.output.error_msg(mod_msg, show_stack=False)
                    elif os.path.exists(self.CheckOutDir.abspath):
                        api.output.verbose_msg(
                            ['scm.update', 'scm'], f'No local modification detected in "{self.CheckOutDir.abspath}", updating...')
                else:
                    ret_val = False
            else:
                ret_val = False
            api.output.verbose_msg(['scm.update', 'scm'], ' smart logic returns value of %s%s' %
                                   (ret_val, ret_val == True and ',update needed' or ''))

        elif self._has_target_match(update) or update == True:
            api.output.verbose_msg(['scm.update', 'scm'], ' --update switch matched, update needed')
            ret_val = True

        # check to see that the last operation was complete
        cache = datacache.GetCache(name=self._env['ALIAS'], key='scm')
        if cache:
            # we only care to check if there is a cache item
            # else we assume everything is OK
            # this prevent un wanted forced check outs cause the cache was
            # being ignored or rebuilt

            # see if it passed last time
            if not cache.get('completed', True):
                api.output.verbose_msg(['scm.update', 'scm'], ' Last action was recorded as failing to complete, update needed')
                ret_val = True
        if ret_val:
            api.output.verbose_msg([['scm.update', 'scm']], ' %s will \033[31mupdate!\033[0m' % (self._pobj.Alias))
        else:
            api.output.verbose_msg([['scm.update', 'scm']], ' %s will \033[32mnot update!\033[0m' % (self._pobj.Alias))
        self.__update_src = ret_val
        return ret_val

    def is_modified(self):
        return False

    def do_update_check(self):
        '''Function that should be used by subclass to add to any custom update logic that should be checked'''

        return False

    def do_exist_logic(self) -> Optional['str']:
        ''' call for testing if the scm think the stuff exists

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        return None

    def do_check_logic(self) -> Optional['str']:
        ''' call for checking if what we have in the data cache is matching the current checkout request
        in the SConstruct match up

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        return None

    def do_force_logic(self) -> Optional['str']:
        ''' call for testing if what is one disk matches what the SConstruct says should be used

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        return None

    def UpdateMirrorOnDisk(self) -> int:
        '''
        This function will update/create the mirror of the object
        '''
        # if we can mirror and we should use the cache
        ret = 0
        if self.canMirror and self.useCache:
            # create the mirror if it does not exist
            if not self.hasMirror:
                ret = self.CreateMirror()
            else:
                ret = self.UpdateMirror()

        # Something went wrong (probally has partial state from a previous failure)
        if ret and self._env.GetOption('scm_retry') == True:
            # we have retry on... we we will give it another try
            # as it could be bad disk state or network glitch
            api.output.print_msg("CreateMirror action failed, restoring clean state.")
            api.output.print_msg('Deleting directory: {}'.format(self.MirrorPath))
            try:
                removeall(self.MirrorPath)
            except OSError as e:
                api.output.error_msg("Failed to remove directory: {0}".format(e), show_stack=False, exit=False)
                raise
            ret = self.CreateMirror()
            if ret:
                api.output.error_msg("CreateMirror action failed again for {0}. Stopping build!".format(
                    self.FullPath), show_stack=False, exit=False)
        return ret

    def UpdateOnDisk(self) -> int:
        '''
        This function does the update logic on the disk.
        The function is large so prevent copy and pasting issues in different
        objects.
        '''

        ret = 0
        # does the part file and checkout directory both exists
        # if it does we just need to update the code
        if (self.PartFileExists or self.isExtern) and self.CheckOutDirExists:
            try:
                try:
                    ret = self.Update()
                except PartRuntimeError as e:
                    ret = True
            except Exception:
                api.output.error_msg("Unexpected exception when doing Update actions for {0}. Stopping build!".format(
                    self._pobj.Alias), show_stack=False, exit=False)
                traceback.print_exc()
                raise
            if ret and ret != 10 and self._env.GetOption('scm_retry') == True:
                astr = "Update"
        else:
            # if these items are missing we need to clone/checkout the code.
            try:
                ret = self.CheckOut()
            except Exception:
                api.output.error_msg("Unexpected exception when Checkout actions for {0}. Stopping build!".format(
                    self._pobj.Alias), show_stack=False, exit=False)
                traceback.print_exc()
                raise
            if ret and self._env.GetOption('scm_retry') == True:
                astr = "Checkout"

        if ret and ret != 10 and self._env.GetOption('scm_retry') == True:
            api.output.print_msg("{0} action failed, restoring clean state for {1}.".format(astr, self._pobj.Alias))
            api.output.print_msg('Deleting directory: %s' % self.CheckOutDir.abspath)
            try:
                removeall(self.CheckOutDir.abspath)
            except OSError as e:
                api.output.error_msg("Failed to remove directory: {0}".format(e), show_stack=False, exit=False)
                raise
            api.output.print_msg("Doing full checkout of {0}.".format(self._pobj.Alias))
            ret = self.CheckOut()
            if ret:
                api.output.error_msg("Checkout action failed again for {0}. Stopping build!".format(
                    self._pobj.Alias), show_stack=False, exit=False)
        return ret

    def clean_step(self, out_dir):
        '''
        Function to allow for any special actions that are needed before we clean.
        @param self object pointer
        @param out_dir The root directory that we want to clean

        normally does nothing but some scm tool make read-only directories with state
        that we want to clean up. Given then the Python will error when trying to clean
        these items. This allow the tool to reset the state to a writable state so the
        scons -c command can correctly clean the data
        '''
        pass

    def CreateMirrorAction(self):
        '''
        Given we can make a mirror. This function will return the action to create the mirror
        '''
        return None

    def UpdateMirrorAction(self):
        '''
        Given we have a mirror. This function will return the action to update the mirror
        '''
        return None

    def UpdateAction(self, out_dir):
        '''
        this is what would be called for any updating of the location

        @param self object pointer
        @param out_dir The location we want to update

        The out_dir value is added to help with fancy scm objects that might want need
        to make and test different action cases
        '''
        return None

    def CheckOutAction(self, out_dir):
        '''
        this is what would be called when we need to get a fresh checkout copy

        @param self object pointer
        @param out_dir The location we want to checkout to

        The out_dir value is added to help with fancy scm objects that might want need
        to make and test different action cases
        '''
        return None

    def CreateMirror(self):
        action = self.CreateMirrorAction()
        return self._env.Execute(action)

    def UpdateMirror(self):
        action = self.UpdateMirrorAction()
        return self._env.Execute(action)

    def Update(self):
        ''' This does the check update logic for a given tool

        Ideally this does not get overridden as the and tool only needs to provide a command to run
        '''

        action = self.UpdateAction(self.CheckOutDir.abspath)
        if action == 10:  # needs to be cleaned first
            return 10
        return self._env.Execute(action)

    def CheckOut(self):
        ''' This does the check update logic for a given tool

        Ideally this does not get overridden as the and tool only needs to provide a command to run
        '''

        action = self.CheckOutAction(self.CheckOutDir.abspath)
        return self._env.Execute(action)

    def ProcessResult(self, result):
        ''' this function returns the result of the given action call.

        @param result True or False based on if the Update logic was able to finish a successfull update

        Allow the a scm object to setup an last minute state that it wants to. or store any data that might be needed
        for the next run
        '''
        pass

    def PostProcess(self):
        ''' This function is called when the system is done with all the update checks and disk updates
        This allows the object to update any data it needs on disk. This is always called.
        '''
        pass

    @staticmethod
    def command_output(cmd_str, echo=False):
        '''
        This internal call is to help with making a system call and printing
        basic error messages

        @param cmd_str the command to run
        @param echo Echo the output to the screen
        @param ret_code object to process the text to provide better reason for failure
        '''

        if echo:
            api.output.print_msg("cmd str=%s" % cmd_str)
        api.output.verbose_msgf('scm_command', "cmd str={0}", cmd_str)
        sys.stdout.flush()

        # try:
        cmd_output = ""
        proc = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True)
        # while command runs get output
        while (proc.poll() is None):
            tmp = proc.stdout.readline()
            if echo:
                sys.stdout.write(tmp)
            cmd_output += tmp
        # when command is done get the rest of the output
        for last_output in proc.stdout.readlines():
            if echo:
                sys.stdout.write(last_output)
            cmd_output += last_output
        if echo:  # print out a new line
            print()
        # get return codes
        ret = proc.returncode
        api.output.verbose_msgf('scm_command', "output={0}", cmd_output)
        proc.stdout.close()
        return (ret, cmd_output)
        # except KeyError:
        #    raise
        # except:
        #    return None

    # Returns name of cache file with scm info
    @property
    def _cache_filename(self):
        # Should be implemented in derived class
        raise NotImplementedError()

    @property
    def CacheFileExists(self):
        if self._cache_filename:
            return os.path.exists(os.sep.join([".parts.cache", 'scm', self._cache_filename + ".cache"]))
        return True  # there is no cache file.. so it can't not exists

# add configuration variable needed for part


api.register.add_bool_variable('UPDATE_ALL', False, 'Controls if Parts will update source from servers')
api.register.add_variable('CHECK_OUT_ROOT', '#_scm', 'Root directory to place checked out data')
api.register.add_variable('CHECK_OUT_DIR', '$SCM_DIR', 'Full path used for any given checked out item')
api.register.add_variable('SCM_DIR', '$VCS_DIR', '')  # backward compatibility
api.register.add_variable('VCS_DIR', '$SCM.CHECKOUT_DIR', '')

# for external part pulls
api.register.add_variable('EXTERN_CHECK_OUT_ROOT', '#_extern', '')
api.register.add_variable('SCM_EXTERN_DIR', '$EXTERN_CHECKOUT_DIR', '')


api.register.add_bool_variable('SCM_IGNORE_MODIFIED', False, '')

api.register.add_variable('SCM_CACHE_ROOT_DIR', '$PART_USER_DIR/.cache/parts/scm', '')
api.register.add_bool_variable('USE_SCM_CACHE', False, '')
