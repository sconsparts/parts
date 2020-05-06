

import os
import re
import stat
import subprocess
import sys
import traceback

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


class base(object):
    '''
    Base object for all VCS (version control systems) objects

    Contain the base logic for all the vcs type objects. All objects should use
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
    ]

    def __init__(self, repository, server=None, use_cache=None):
        '''Constructor for the vcs object
        @param self The object pointer
        @param repository The location under in the server to find get the data files
        @param server The vcs server to access. If not provided the full value of the repository value is used
        '''

        self._repository = repository
        self._server = server
        self._allow_parallel = True
        self._pobj = None
        self._env = None
        self._full_path = None
        self._use_cache = use_cache

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
    def useCache(self) -> bool:
        '''
        Returns true if there is a mirror found
        '''
        if self._use_cache is None:
            return self._env.subst("$USE_SCM_CACHE", False)
        else:
            return self._use_cache

    @property
    def Server(self):
        '''returns the value of the server

        Subclasses may add to this logic as they might want to define other values to fall back on if the
        server value if None. For example the SVN object will return the value of $SVN_SERVER if the
        server is not set
        '''
        return self._server

    @property
    def Repository(self):
        '''returns the value of the server

        Subclasses may add to this logic as they might want to define other values based on custom logic.
        '''
        return self._repository

    @property
    def CheckOutDir(self):
        '''returns the path in which we want to checkout to'''
        return self._env.Dir('$CHECK_OUT_DIR').srcnode()

    @property
    def PartFileName(self):
        '''returns the modifed path of the Parts file based on the check out directory'''
        return self._env.Dir(self.CheckOutDir).File(self._pobj.File)

    @property
    def PartFileExists(self):
        return os.path.exists(self.PartFileName.abspath)

    @property
    def CheckOutDirExists(self):
        return os.path.exists(self.CheckOutDir.abspath)

    @property
    def FullPath(self):
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
        ''' This sets up the vcs object data for real use
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
        Update the with information about the current VCS object
        '''
        self._env['VCS'] = common.namespace(
            TYPE='unknown',
            CHECKOUT_DIR=''
        )

    def _has_target_match(self, update_option):

        if util.isList(update_option):
            for i in update_option:
                target = target_type.target_type(i)
                tmp = part_ref.part_ref(target)
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

    def NeedsToUpdate(self):
        '''Tell us if this Vcs object believe it need to be updated'''
        ret_val = False
        update = self._env.GetOption('update')
        api.output.verbose_msg('vcs_update', 'Vcs update check for part: "%s"' % self._pobj.Alias)
        # do custom check
        if self.do_update_check():
            api.output.verbose_msg('vcs_update', ' do_update_check (custom checks) requires updating')
            ret_val = True
        elif update == 'auto':
            # do smart logic stuff
            # get the scm-logic value

            logic_type = self._env.GetOption('vcs_logic')
            api.output.verbose_msg('vcs_update', ' doing smart logic of "%s"' % logic_type)
            if logic_type == 'exists':
                ret = self.do_exist_logic()
            elif logic_type == 'check':
                ret = self.do_check_logic()
            elif logic_type == 'force':
                ret = self.do_force_logic()
            elif logic_type == 'none':
                ret = False
                return ret
            mod_msg = 'Local modification detected in "{0}".\n Add --update to force update for merge and potential loss of local changes'.format(
                self.CheckOutDir.abspath)
            if ret:
                # get policy for how to handle a positive response
                pol = self._env.GetOption('vcs_policy')
                api.output.verbose_msgf('vcs_update', "update policy is '{0}'", pol)
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
                        api.output.verbose_msg('vcs_update', ret)
                    else:
                        # report the warning
                        api.output.warning_msg(ret, show_stack=False)
                        api.output.warning_msg(
                            "Add --update to force update for merge and potential loss of local changes", show_stack=False)
                elif pol == 'checkout-error':
                    ret_val = False
                    if self.do_exist_logic():
                        api.output.verbose_msg('vcs_update', ret)
                    else:
                        # report the error
                        api.output.error_msg(ret, show_stack=False, exit=False)
                        api.output.error_msg(
                            "Add --update to force update for merge and potential loss of local changes", show_stack=False)
                elif pol == 'message-update':
                    ret_val = True
                    api.output.print_msg(ret)
                    if self.is_modified():
                        api.output.error_msg(mod_msg, show_stack=False)
                    elif os.path.exists(self.CheckOutDir.abspath):
                        api.output.print_msg(
                            'No local modification detected in "{0}", updating...'.format(self.CheckOutDir.abspath))
                elif pol == 'warning-update':
                    ret_val = True
                    api.output.warning_msg(ret, show_stack=False)
                    if self.is_modified():
                        api.output.error_msg(mod_msg, show_stack=False)
                    elif os.path.exists(self.CheckOutDir.abspath):
                        api.output.warning_msg('No local modification detected in "{0}", updating...'.format(
                            self.CheckOutDir.abspath), show_stack=False)
                elif pol == 'update':
                    ret_val = True
                    api.output.verbose_msg('vcs_update', ret)
                    if self.is_modified():
                        api.output.error_msg(mod_msg, show_stack=False)
                    elif os.path.exists(self.CheckOutDir.abspath):
                        api.output.verbose_msg(
                            'vcs_update', 'No local modification detected in "{0}", updating...'.format(self.CheckOutDir.abspath))
                else:
                    ret_val = False
            else:
                ret_val = False
            api.output.verbose_msg('vcs_update', ' smart logic returns value of %s%s' %
                                   (ret_val, ret_val == True and ',update needed' or ''))

        elif self._has_target_match(update) or update == True:
            api.output.verbose_msg('vcs_update', ' --update switch matched, update needed')
            ret_val = True

        # this check the backwards compatible way.. to be removed
        # @todo remove this case in 0.10+1.0 version
        elif self._env.get('UPDATE_' + self._env['PART_ALIAS'].upper(), None) is not None or self._pobj.Env['UPDATE_ALL'] == True:
            api.output.verbose_msg('vcs_update', ' Backward compatibility check requires updating')
            ret_val = True

        # check to see that the last operation was complete
        cache = datacache.GetCache(name=self._env['ALIAS'], key='vcs')
        if cache:
            # we only care to check if there is a cache item
            # else we assume everything is OK
            # this prevent un wanted forced check outs cause the cache was
            # being ignored or rebuilt

            # see if it passed last time
            if cache.get('completed', True) != True:
                api.output.verbose_msg('vcs_update', ' Last action was recorded as failing to complete, update needed')
                ret_val = True
        if ret_val:
            api.output.verbose_msg(['vcs_update'], ' %s will \033[31mupdate!\033[0m' % (self._pobj.Alias))
        else:
            api.output.verbose_msg(['vcs_update'], ' %s will \033[32mnot update!\033[0m' % (self._pobj.Alias))
        return ret_val

    def is_modified(self):
        return False

    def do_update_check(self):
        '''Function that should be used by subclass to add to any custom update logic that should be checked'''

        return False

    def do_exist_logic(self):
        ''' call for testing if the vcs think the stuff exists

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        return None

    def do_check_logic(self):
        ''' call for checking if what we have in the data cache is matching the current checkout request
        in the SConstruct match up

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        return None

    def do_force_logic(self):
        ''' call for testing if what is one disk matches what the SConstruct says should be used

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        return None

    def UpdateOnDisk(self) -> int:
        '''
        This function does the update logic on the disk.
        The function is large so prevent copy and pasting issues in different
        objects.
        '''
        ##############################################
        # start with mirror
        #############################################
        # if we can mirror and we should use the cache
        ret = False
        if self.canMirror and self.useCache:
            # create the mirror if it does not exist
            if not self.hasMirror:
                ret = self.CreateMirror()
            else:
                ret = self.UpdateMirror()

        # Something went wrong ( probally does not exists)
        if ret and self._env.GetOption('vcs_retry') == True:
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

        if self.PartFileExists and self.CheckOutDirExists:
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
            if ret and ret != 10 and self._env.GetOption('vcs_retry') == True:
                astr = "Update"
        else:
            try:
                ret = self.CheckOut()
            except Exception:
                api.output.error_msg("Unexpected exception when Checkout actions for {0}. Stopping build!".format(
                    self._pobj.Alias), show_stack=False, exit=False)
                traceback.print_exc()
                raise
            if ret and self._env.GetOption('vcs_retry') == True:
                astr = "Checkout"

        if ret and ret != 10 and self._env.GetOption('vcs_retry') == True:
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

        normally does nothing but some vcs tool make read-only directories with state
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

        The out_dir value is added to help with fancy vcs objects that might want need
        to make and test different action cases
        '''
        return None

    def CheckOutAction(self, out_dir):
        '''
        this is what would be called when we need to get a fresh checkout copy

        @param self object pointer
        @param out_dir The location we want to checkout to

        The out_dir value is added to help with fancy vcs objects that might want need
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

        Allow the a vcs object to setup an last minute state that it wants to. or store any data that might be needed
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
        api.output.verbose_msgf('vcs_command', "cmd str={0}", cmd_str)
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
        api.output.verbose_msgf('vcs_command', "output={0}", cmd_output)
        proc.stdout.close()
        return (ret, cmd_output)
        # except KeyError:
        #    raise
        # except:
        #    return None

    # Returns name of cache file with vcs info
    @property
    def _cache_filename(self):
        # Should be implemented in derived class
        raise NotImplementedError()

    @property
    def CacheFileExists(self):
        if self._cache_filename:
            return os.path.exists(os.sep.join([".parts.cache", 'vcs', self._cache_filename + ".cache"]))
        return True  # there is no cache file.. so it can't not exists

# add configuartion varaible needed for part


api.register.add_bool_variable('UPDATE_ALL', False, 'Controls if Parts will update source from servers')
api.register.add_variable('CHECK_OUT_ROOT', '#_vcs', 'Root directory to place checked out data')
api.register.add_variable('CHECK_OUT_DIR', '$VCS_DIR', 'Full path used for any given checked out item')
api.register.add_variable('VCS_DIR', '$VCS.CHECKOUT_DIR', '')

api.register.add_variable('SCM_CACHE_ROOT_DIR', '$PART_USER_DIR/.cache/parts/scm', '')
api.register.add_bool_variable('USE_SCM_CACHE', False, '')
