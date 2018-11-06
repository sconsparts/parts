from __future__ import absolute_import, division, print_function

import os
import re

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

import parts.api as api
import parts.common as common
import parts.datacache as datacache
from parts.core import util

from .base import base, removeall


class git(base):
    ''' This is the implmentation of the vcs GIT logic'''

    __slots__ = [
        '__branch',
        '_disk_data',
        '_completed',
        '_method',
        '_patchfile',
    ]
    gitpath = None  # the path to the git program to run

    def __init__(self, repository, server=None, method=None, branch='master', tag=None, patchfile=None, **kw):
        '''Constructor call for the GIT object
        @param repository The repository or path from server under the server to get our data from
        @param server The server to connect to
        @param branch The optional branch to use after the clone, or on an update
        @param remote_branches Optional remote branches to add to the clone for tracking
        '''
        self.__branch = branch
        self._disk_data = None
        self._completed = None
        self._method = method
        self._patchfile = patchfile
        if repository.endswith('.git'):
            repository = repository[:-4]
        if server and server.endswith('/'):
            server = server[:-1]

        self.__branch = tag
        super(git, self).__init__(repository, server)

    def _branch_changed(self, data):
        return data['branch'] != "{0}...origin/{0}".format(self.__branch) and self.__branch not in data['tags']

    def _on_tag(self, data):
        return self.__branch in data['tags']

    def _server_changed(self, data):
        return data['server'] != self.FullPath

    def _setup_(self, *lst, **kw):
        base._setup_(self, *lst, **kw)
        if self._server:
            self._server = self._server[:-1]

    @base.FullPath.getter
    def FullPath(self):
        if self._method == "git":
            self._full_path = "git@{server}:{repo}.git".format(server=self.Server, repo=self.Repository)
        else:
            self._full_path = "https://{server}/{repo}.git".format(server=self.Server, repo=self.Repository)
        return self._full_path

    @base.Server.getter
    def Server(self):
        ''' git property override to getting server data'''
        if self._server is not None:
            return self._server
        return self._env['GIT_SERVER']

    def UpdateAction(self, out_dir):
        '''
        Returns the update Action for GIT

        Checks to see what set we need to do.  
        '''
        # todo add the ability to stash changes for the user...
        # if the server is different we need to relocate
        #update_path = self.FullPath

        # clean actions.. use if --vcs-clean is set
        cmd1 = 'cd {0} && "{1}" clean -dfx --force && "{1}" reset --hard'.format(out_dir, git.gitpath)
        strval1 = 'cd {0} && {1} clean -dfx --force && "{1}" reset --hard'.format(out_dir, 'git')
        clean_action = [
            self._env.Action(cmd1, strval1)
        ]

        # Fetch action to update with correct branch/tag
        cmd1 = 'cd {0} && "{1}" fetch'.format(out_dir, git.gitpath)
        strval1 = 'cd {0} && {1} fetch'.format(out_dir, 'git')
        fetch_action = [
            self._env.Action(cmd1, strval1)
        ]

        # we do this switch to the correct branch/tag
        if self.__branch is None:
            branch = 'master'
        else:
            branch = self.__branch
        cmd1 = 'cd {0} && "{1}" checkout {2}'.format(out_dir, git.gitpath, branch)
        strval1 = 'cd {0} && {1} checkout {2}'.format(out_dir, 'git', branch)
        checkout_action = [
            self._env.Action(cmd1, strval1)
        ]

        # we do this with a update request on if we are not on a tag
        cmd1 = 'cd {0} && "{1}" pull'.format(out_dir, git.gitpath)
        strval1 = 'cd {0} && {1} pull'.format(out_dir, 'git')
        pull_action = [
            self._env.Action(cmd1, strval1)
        ]

        ret = []
        do_clean = self._env.GetOption('vcs_clean')
        do_retry = self._env.GetOption('vcs_retry')
        data = self.get_git_data()

        # do we have data?
        if data is None:
            # we have some bad state
            # could happen if check policy is existance or cache and user messed around
            if do_clean or do_retry:
                ret = [
                    self._env.Action(
                        lambda target, source, env: removeall(out_dir),
                        "Cleaning up checkout area for {0}".format(out_dir)
                    )
                ] + self.CheckOutAction(out_dir)

            else:
                # if it they are not set we want to say something is up.. give me the power to fix it, or do something about it
                api.platforms.output.error_msg(
                    'Directory "{0}" already exists with no .git directory. Manually remove directory or update with --vcs-retry or --vcs-clean'.format(out_dir), show_stack=False)
        else:
            server_disk = data['server']
            server_changed = self._server_changed(data)
            branch = data['branch']
            tags = data['tags']
            branch_changed = self._branch_changed(data)
            on_tag = self._on_tag(data)

            # first check to see if we want to a clean setup
            # this will remove and reset the branch
            if do_clean:
                ret += clean_action
            # if we changed we will do a fetch and a checkout to new branch
            if branch_changed:
                # do fetch to get data
                ret += fetch_action
                # do the checkout
                ret += checkout_action
            elif not on_tag:
                # branch did not change
                ret += pull_action

        return ret

    def CheckOutAction(self, out_dir):
        '''
        Returns the action to do the checkout
        if it is Branch is None we assume that "checked out" code
        is what is wanted ( ie the "master" branch)
        If it is not None we try to switch to it after the checkout
        Note this is only useful if one sets remote_branches to track
        '''

        # this is a little cheat at the moment. Git seem to handle only
        # single level directory outputs at the moment. So we create the
        # directory for Git to be nice. might break the -dryrun logic
        # but that is already broken in terms of directory creation
        # at the moment in scons
        # print os.path.exists(out_dir)
        # if not os.path.exists(out_dir):
        # os.makedirs(out_dir)

        # the intial clone
        git_out_path = out_dir.replace('\\', '/')
        clone_path = self.FullPath

        if self.__branch:
            branch = "-b {}".format(self.__branch)
        else:
            branch = ''
        strval = '{0} clone --progress {branch} {1} "{2}"'.format(git.gitpath, clone_path, git_out_path, branch=branch)
        cmd = '"{0}" clone --progress {branch} {1} "{2}"'.format(git.gitpath, clone_path, git_out_path, branch=branch)

        ret = [self._env.Action(cmd, strval)]

        # have patch file .. apply it
        if self._patchfile:
            fullpath = self._env.File(self._patchfile).abspath
            strval = 'cd {0} && {1} am "{2}"'.format(out_dir, git.gitpath, fullpath)
            cmd = 'cd {0} && "{1}" am "{2}"'.format(out_dir, git.gitpath, fullpath)
            ret += [self._env.Action(cmd, strval)]

        return ret

    def clean_step(self, out_dir):
        ''' since git tends to checkout the .git meta data area as readonly
        it turns out that we can't clean the checked out code correctly as
        python will not clean the files that are readonly. This makes it so
        all the data is writable so we can do the delete actions
        '''

        import stat
        # small Hack to turn off read only access so we can delete
        # the mess via -clean
        for root, dirs, files in os.walk(out_dir, topdown=False):
            for f in files:
                source = os.path.join(root, f)
                st = os.stat(source)
                os.chmod(source, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)
            for f in dirs:
                source = os.path.join(root, f)
                st = os.stat(source)
                os.chmod(source, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)

    def do_update_check(self):
        '''Function that should be used by subclass to add to any custom update logic that should be checked'''
        return False

    def do_exist_logic(self):
        ''' call for testing if the vcs think the stuff exists that should be build

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        api.output.verbose_msg(["vcs_update", "vcs_git"], " Doing existance check")
        if self.PartFileExists and os.path.exists(os.path.join(self.CheckOutDir.abspath, '.git')):
            return None
        api.output.verbose_msg(["vcs_update", "vcs_git"], " Existance check failed")
        return "{0} needs to be updated on disk" .format(self._pobj.Alias)

    def do_check_logic(self):
        ''' call for checking if what we have in the data cache is matching the current checkout request
        in the SConstruct match up

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        # todo.. fix issue with mismatch branch/tag being used

        api.output.verbose_msg(["vcs_update", "vcs_git"], " Using vcs-logic: check.")
        # test for existance
        tmp = self.do_exist_logic()
        if tmp:
            return tmp
        # get data cache and see if our paths match
        cache = datacache.GetCache(name=self._env['ALIAS'], key='vcs')
        if cache:
            api.output.verbose_msg(["vcs_update", "vcs_git"], " Cached server: %s" % (cache['server']))
            api.output.verbose_msg(["vcs_update", "vcs_git"], " Requested Server: %s" % (self.FullPath))
            if cache['server'] != self.FullPath:
                api.output.verbose_msg(["vcs_update", "vcs_git"], " Cache version of server does not match.. verifing on disk..")
                # hard check to verify it is really bad
                data = self.get_git_data()
                if data:
                    if data['url'] != self.FullPath:
                        api.output.verbose_msg(["vcs_update", "vcs_git"], " Disk urls does not match")
                        return 'Server on disk is different than the one requested for Parts "%s"\n On disk: %s\n requested: %s' % (self._pobj.Alias, data[
                                                                                                                                    'server'], self.FullPath)
                else:
                    api.output.verbose_msg(["vcs_update", "vcs_git"], " Could not query disk version for information!")
                    return 'Disk copy seems bad... updating'
            api.output.verbose_msg(["vcs_update", "vcs_git"], " Disk urls matches")
            # check branch
            api.output.verbose_msg(["vcs_update", "vcs_git"], " Cached branch: %s" % (cache['branch']))
            api.output.verbose_msg(["vcs_update", "vcs_git"], " Requested branch: %s" % (self.__branch))
            if cache['branch'] != self.__branch:
                api.output.verbose_msg(["vcs_update", "vcs_git"], " Cache version of branch does not match.. verifing on disk..")
                # hard check to verify it is really bad
                data = self.get_git_data()
                if data:
                    if data['branch'] != "{0}...origin/{0}".format(self.__branch) and self.__branch not in data['tags']:
                        api.output.verbose_msg(["vcs_update", "vcs_git"], " Disk branch does not match")
                        return 'Branch on disk is different than the one requested for Parts "%s"\n On disk: %s\n requested: %s' % (self._pobj.Alias, data[
                                                                                                                                    'branch'], self.__branch)
                else:
                    api.output.verbose_msg(["vcs_update", "vcs_git"], " Could not query disk version for information!")
                    return 'Disk copy seems bad... updating'
            api.output.verbose_msg(["vcs_update", "vcs_git"], " Disk branch matches")

        else:
            api.output.verbose_msg(["vcs_update", "vcs_git"], " Data Cache does not exist.. doing force logic")
            return self.do_force_logic()

    def do_force_logic(self):
        ''' call for testing if what is one disk matches what the SConstruct says should be used

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        api.output.verbose_msg(["vcs_update", "vcs_git"], " Using force vcs logic.")
        # test for existance
        tmp = self.do_exist_logic()
        if tmp:
            api.output.verbose_msg(["vcs_update", "vcs_git"], " Existance checked failed")
            return tmp
        data = self.get_git_data()
        if data:
            if data['server'] != self.FullPath:
                api.output.verbose_msg(["vcs_update", "vcs_git"], " Disk checked failed")
                return 'Server on disk is different than the one requested for Parts "%s"\n On disk: %s\n requested: %s' % (self._pobj.Alias, data[
                    'server'], self.FullPath)
            if data['branch'] != "{0}...origin/{0}".format(self.__branch) and self.__branch not in data['tags']:
                api.output.verbose_msg(["vcs_update", "vcs_git"], " Disk branch does not match")
                return 'Branch on disk is different than the one requested for Parts "%s"\n On disk: %s\n requested: %s' % (self._pobj.Alias, data[
                    'branch'], self.__branch)

    def UpdateEnv(self):
        '''
        Update the with information about the current VCS object
        '''
        if git.gitpath is None:
            tmp = self._env.WhereIs('git')
            if not tmp:
                tmp = self._env.WhereIs('git', os.environ['PATH'])
            if not tmp:
                api.output.error_msg("Could find git on the system!", show_stack=False)
            git.gitpath = tmp

        if self._env['HOST_OS'] == 'win32':
            try:
                self._env['ENV']['GIT_SSH'] = os.environ['GIT_SSH']
            except KeyError:
                pass

        self._env['VCS'] = common.namespace(
            TYPE='git',
            CHECKOUT_DIR='$VCS_GIT_DIR',
            TOOL=git.gitpath,
            SERVER_PATH=self.FullPath,
            MODIFIED=common.DelayVariable(lambda: self.get_git_data()['modified']),
            UNTRACKED=common.DelayVariable(lambda: self.get_git_data()['untracked']),
            BRANCH=common.DelayVariable(lambda: self.get_git_data()['branch']),
        )

    def ProcessResult(self, result):
        ''' Handle GIT logic we want need to handle

        @param result True or False based on if the Update logic was able to finish a successfull update

        '''
        # Setup and store vcs data cache logic
        self._completed = result

    def PostProcess(self):
        ''' This function is called when the system is done updating the disk
        This allows the object to update any data it needs on disk, or in the environment
        '''
        if self._completed is None:
            self._completed = True

        tmp = {
            '__version__': 1.0,
            'type': 'git',
            'server': self.FullPath,
            'branch': self.__branch,
            'completed': self._completed
        }

        datacache.StoreData(name=self._cache_filename, data=tmp, key='vcs')

    def is_modified(self):
        return self.get_git_data()['modified']

    def get_git_data(self):
        # get current state
        if self._disk_data is None:
            self._disk_data = GetGitData(self._env, self.CheckOutDir.abspath)
        return self._disk_data

    @property
    def _cache_filename(self):
        return self._env['ALIAS']


def GetGitData(env, checkoutdir=None):

    server = None
    url = None
    modified = False
    switched = False
    partial = False
    rev_low = None
    rev_high = None

    if checkoutdir is None:
        checkoutdir = env.AbsDir('.')

    if git.gitpath is None:
        git.gitpath = env.WhereIs('git', os.environ['PATH'])
        git.gitpath = '{0}'.format(git.gitpath)

    if env['HOST_OS'] == 'win32':
        try:
            env['ENV']['GIT_SSH'] = os.environ['GIT_SSH']
        except KeyError:
            pass

    # get some state
    ret, data = base.command_output('cd {1} && "{0}" status -s -b'.format(git.gitpath, checkoutdir))
    modified = False
    untracked = False
    branch = ''
    if not ret:
        data.replace('\r\n', '\n')
        # first line is the ## branch
        # check that we have this, else we have some serious error
        if not data.startswith("##"):
            # we have an error.. fix me
            return

        lines = data.split('\n')
        branch = lines[0].split()[1]
        lines[1:]
        for line in lines:
            # we loop to see if we have
            # have untracked or modifed state
            # if both become true we stop, else we iter
            # the whole set of data
            if line.startswith("??"):
                untracked = True
            else:
                modified = True
            if untracked and modified:
                break

    # get tags as these might be the "branch" we are on
    ret, data = base.command_output('cd {1} && "{0}" tag --points-at HEAD'.format(git.gitpath, checkoutdir))
    if not ret:
        data.replace('\r\n', '\n')
    tags = data.split('\n')[:-1]
    # get the server we will pull from
    ret, data = base.command_output('cd {1} && "{0}" remote -v'.format(git.gitpath, checkoutdir))

    server = ''
    if not ret:
        data.replace('\r\n', '\n')
        lines = data.split('\n')
        for line in lines:
            tmp = line.split()

            if tmp[0] == 'origin' and tmp[2] == '(fetch)':
                server = tmp[1]
                break

    ret = {
        'branch': branch,
        'tags': tags,
        'modified': modified,
        'untracked': untracked,
        'server': server,
        'url': url
    }

    return ret


# add configuartion varaible needed for part
api.register.add_variable('GIT_SERVER', '', '')
api.register.add_variable('GIT_USER', '$PART_USER', '')
api.register.add_variable('VCS_GIT_DIR', '${CHECK_OUT_ROOT}/${PART_ALIAS}', '')

api.register.add_global_object('VcsGit', git)

SConsEnvironment.GitInfo = GetGitData
