from __future__ import absolute_import, division, print_function

import os
import re

import parts.api as api
import parts.common as common
import parts.datacache as datacache
import parts.version as version
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

from .base import base, removeall


def _get_gitpath(env):
    if git.gitpath is None:
        tmp = env.WhereIs('git')
        if not tmp:
            tmp = env.WhereIs('git', os.environ['PATH'])
        if not tmp:
            api.output.error_msg("Could find git on the system!", show_stack=False)
        return tmp
    else:
        tmp = _get_gitpath
    return tmp


class git(base):
    ''' This is the implementation of the vcs GIT logic'''

    __slots__ = [
        '__branch',
        '__revision',
        '_disk_data',
        '_completed',
        '_protocol',
        '_patchfile',
    ]
    gitpath = None  # the path to the git program to run

    def __init__(self, repository, server=None, protocol=None, branch=None, tag=None, revision=None, patchfile=None, **kw):
        '''Constructor call for the GIT object
        @param repository The repository or path from server under the server to get our data from
        @param server The server to connect to
        @param branch The optional branch to use after the clone, or on an update
        @param remote_branches Optional remote branches to add to the clone for tracking
        '''
        self.__branch = branch
        self.__revision = revision
        self._disk_data = None
        self._completed = None
        self._protocol = protocol
        self._patchfile = patchfile
        if repository.endswith('.git'):
            repository = repository[:-4]
        if server and server.endswith('/'):
            server = server[:-1]

        if branch and tag or branch and revision or tag and revision:
            api.output.error_msgf(
                "Only one argument of 'branch', 'tag' or 'revision' can be set at a time. \n"
                " tag={tag}\n branch={branch}\n revision={revision}",
                branch=branch,
                tag=tag,
                revision=revision)

        if tag:
            self.__branch = tag

        super(git, self).__init__(repository, server)

    def _branch_changed(self, data):
        return data['branch'] != "{0}...origin/{0}".format(self.__branch) and self.__branch not in data['tags']

    def _on_tag(self, data):
        return self.__branch in data['tags']

    def _server_changed(self, data):
        return data['server'] != self.FullPath

    @base.FullPath.getter
    def FullPath(self):
        if not self._full_path:
            protocol = self._protocol if self._protocol else self._env['GIT_PROTOCOL']
            if protocol == "git":
                self._full_path = "git@{server}:{repo}.git".format(server=self.Server, repo=self.Repository)
            elif protocol == "https":
                self._full_path = "https://{server}/{repo}.git".format(server=self.Server, repo=self.Repository)
            else:
                api.output.error_msgf("Unknown git protocol provided. Must be 'https' or 'git'")
        return self._full_path

    @base.Server.getter
    def Server(self):
        ''' git property override to getting server data'''
        if self._server is not None:
            ret = self._server
        else:
            ret = self._env['GIT_SERVER']
        if ret.endswith("/"):
            ret = ret[:-1]
        return ret

    def UpdateAction(self, out_dir):
        '''
        Returns the update Action for GIT

        Checks to see what set we need to do.
        This assumes stuff is on disk already
        '''

        # if the server is different we need to relocate
        update_path = self.FullPath

        # change repo
        cmd1 = 'cd {0} && "{1}" remote set-url origin {origin}'.format(out_dir, git.gitpath, origin=update_path)
        strval1 = 'cd {0} && {1} remote set-url origin {origin}'.format(out_dir, 'git', origin=update_path)
        origin_change_action = [
            self._env.Action(cmd1, strval1)
        ]

        # clean actions.. use if --vcs-clean is set
        cmd1 = 'cd {0} && "{1}" clean -dfx --force'.format(out_dir, git.gitpath)
        strval1 = 'cd {0} && {1} clean -dfx --force'.format(out_dir, 'git')
        clean_action = [
            self._env.Action(cmd1, strval1)
        ]

        # Fetch action to update with correct branch/tag
        cmd1 = 'cd {0} && "{1}" fetch ${{GIT_FETCH_ARGS}}'.format(out_dir, git.gitpath)
        strval1 = 'cd {0} && {1} fetch ${{GIT_FETCH_ARGS}}'.format(out_dir, 'git')
        fetch_action = [
            self._env.Action(cmd1, strval1)
        ]

        # we do this switch to the correct branch/tag/revision
        # need to get correct value as the "checkout" takes any value
        if self.__revision:
            branch = self.__revision
        elif self.__branch is None:
            branch = self._env["GIT_DEFAULT_BRANCH"]
        else:
            branch = self.__branch
        cmd1 = 'cd {0} && "{1}" checkout ${{GIT_CHECKOUT_ARGS}} {2}'.format(out_dir, git.gitpath, branch)
        strval1 = 'cd {0} && {1} checkout ${{GIT_CHECKOUT_ARGS}} {2}'.format(out_dir, 'git', branch)
        checkout_action = [
            self._env.Action(cmd1, strval1)
        ]

        # we do this with a update request only if we are not on a tag
        cmd1 = 'cd {0} && "{1}" pull ${{GIT_PULL_ARGS}}'.format(out_dir, git.gitpath)
        strval1 = 'cd {0} && {1} pull ${{GIT_PULL_ARGS}}'.format(out_dir, 'git')
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
            # could happen if check policy is existence or cache and user messed around
            if do_clean or do_retry:
                ret = [
                    self._env.Action(
                        lambda target, source, env: removeall(out_dir),
                        "Cleaning up checkout area for {0}".format(out_dir)
                    )
                ] + self.CheckOutAction(out_dir)

            else:
                # if it they are not set we want to say something is up.. give me the power to fix it, or do something about it
                api.output.error_msg(
                    'Directory "{0}" already exists with no .git directory.\n Manually remove directory or\n'
                    ' update with --vcs-retry or --vcs-clean'.format(out_dir),
                    show_stack=False)
        else:
            if data['modified'] and not do_clean:
                # check that we don't have modification locally. if we do complain to be safe
                api.output.error_msg(
                    'Local modification found in "{0}".\n Manually commit and push changes or\n update with --vcs-clean'.format(
                        out_dir),
                    show_stack=False
                )
            if data['untracked'] and self._env['GIT_IGNORE_UNTRACKED'] == False and not do_clean:
                # check that we don't have untracked files locally. if we do complain to be safe.
                api.output.error_msg(
                    'Untracked files found in "{0}".\n Manually commit and push changes\n'
                    ' or set variable GIT_IGNORE_UNTRACKED to True\n or update with --vcs-clean'.format(
                        out_dir),
                    show_stack=False)

            server_changed = self._server_changed(data)
            # if branch or tag changed
            branch_changed = self._branch_changed(data)
            # are we on a tag or branch
            on_tag = self._on_tag(data)
            on_revision = self.__revision

            prefix = 'origin/'
            if self.__revision or on_tag:
                prefix = ''
            # hard reset_action
            cmd1 = 'cd {0} && "{1}" reset ${{GIT_RESET_ARGS}} --hard {prefix}{origin}'.format(
                    out_dir, git.gitpath, origin=branch, prefix=prefix)
            strval1 = 'cd {0} && {1} reset ${{GIT_RESET_ARGS}} --hard {prefix}{origin}'.format(
                    out_dir, 'git', origin=branch, prefix=prefix)
            hard_reset_action = [
                self._env.Action(cmd1, strval1)
            ]

            # first check to see if we want to a clean setup
            # this will remove and reset the branch
            if do_clean:
                ret += clean_action+hard_reset_action
            # if the server changed we need to reset the origin to the new value
            if server_changed:
                # we cannot change if we are modified and not cleaning
                if self.is_modified() and not do_clean:
                    api.output.error_msg(
                        'Cannot change remote origin. Local modification found in "{0}".\n'
                        ' Manually commit and push changes or\n update with --vcs-clean'.format(
                            out_dir),
                        show_stack=False)
                # change origin
                ret += origin_change_action
                # do fetch to get data
                ret += fetch_action
                if not branch_changed or on_revision or on_tag:
                    # we can do a hard reset to the location in question
                    ret += hard_reset_action
                elif branch_changed:
                    # do the hard reset to location
                    ret += checkout_action
                    # to be safe
                    ret += hard_reset_action
            # if we changed we will do a fetch and a checkout to new branch
            elif branch_changed:
                # do fetch to get data
                ret += fetch_action
                # do the checkout
                ret += checkout_action                
            elif not on_tag:
                # branch did not change
                if not do_clean:
                    ret += pull_action

            # reapply the patch if any
            if self._patchfile:
                fullpath = self._env.File(self._patchfile).abspath
                strval = 'cd {0} && {1} am ${{GIT_AM_ARGS}} "{2}"'.format(out_dir, git.gitpath, fullpath)
                cmd = 'cd {0} && "{1}" am ${{GIT_AM_ARGS}} "{2}"'.format(out_dir, git.gitpath, fullpath)
                ret += [self._env.Action(cmd, strval)]

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

        # the initial clone
        git_out_path = out_dir.replace('\\', '/')
        clone_path = self.FullPath

        if self.__branch:
            branch = '-b {}'.format(self.__branch)
        elif self.__revision:
            branch = ''
        else:
            # Default or revision case
            # as only tags and branch can be cloned and checked out in one command
            branch = '-b {}'.format(self._env["GIT_DEFAULT_BRANCH"])

        strval = '{0} clone ${{GIT_CLONE_ARGS}} --progress {branch} {1} "{2}"'.format(
                git.gitpath, clone_path, git_out_path, branch=branch)
        cmd = '"{0}" clone ${{GIT_CLONE_ARGS}} --progress {branch} {1} "{2}"'.format(
                git.gitpath, clone_path, git_out_path, branch=branch)
        ret = [self._env.Action(cmd, strval)]

        # if this is a revision we want to checkout that revision
        if self.__revision:
            cmd = 'cd {0} && "{1}" checkout ${{GIT_CHECKOUT_ARGS}} {2}'.format(out_dir, git.gitpath, self.__revision)
            strval = 'cd {0} && {1} checkout ${{GIT_CHECKOUT_ARGS}} {2}'.format(out_dir, 'git', self.__revision)
            ret += [self._env.Action(cmd, strval)]

        # have patch file .. apply it
        if self._patchfile:
            fullpath = self._env.File(self._patchfile).abspath
            strval = 'cd {0} && {1} am ${{GIT_AM_ARGS}} "{2}"'.format(out_dir, git.gitpath, fullpath)
            cmd = 'cd {0} && "{1}" am ${{GIT_AM_ARGS}} "{2}"'.format(out_dir, git.gitpath, fullpath)
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
        api.output.verbose_msg(["vcs_update", "vcs_git"], " Doing existence check")
        if self.PartFileExists and os.path.exists(os.path.join(self.CheckOutDir.abspath, '.git')):
            return None
        api.output.verbose_msg(["vcs_update", "vcs_git"], " Existence check failed")
        return "{0} needs to be updated on disk" .format(self._pobj.Alias)

    def do_check_logic(self):
        '''
        Check that the value we have in the cache matches what was passed in
        This is faster than having forced git checks for larger builds
        Will check that something exists on disk
        Will fallback to a diskchecks if cache sees mismatches to verify it is really
        out of date.

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        failed = False
        api.output.verbose_msg(["vcs_update", "vcs_git"], " Using vcs-logic: check.")
        # test for existence
        tmp = self.do_exist_logic()
        if tmp:
            return tmp
        # get data cache and see if our paths match
        cache = datacache.GetCache(name=self._env['ALIAS'], key='vcs')

        if cache:
            api.output.verbose_msgf(["vcs_update", "vcs_git"], " Cached server:    '{0}'", cache['server'])
            api.output.verbose_msgf(["vcs_update", "vcs_git"], " Requested Server: '{0}'", self.FullPath)

            # do the locations we fetch from match??
            if cache['server'] != self.FullPath:
                api.output.verbose_msg(["vcs_update", "vcs_git"], " Cache version of server does not match.. verifying on disk..")
                failed = True

            else:
                api.output.verbose_msg(["vcs_update", "vcs_git"], " Disk urls matches")
            # the path seems to be matching still.
            # check that what we want to pull matches ( ie branch tag or revision)
            if not failed and self.__revision:
                api.output.verbose_msgf(["vcs_update", "vcs_git"], " Cached revision: {0}", cache['revision'])
                api.output.verbose_msgf(["vcs_update", "vcs_git"], " Requested revision: {0}", self.__revision)
                if cache['revision'] != self.__revision and cache['revision'] != self.__revision[:9]:
                    api.output.verbose_msg(["vcs_update", "vcs_git"],
                                           " Cache version of revision does not match.. verifying on disk..")
                    failed = True
                else:
                    api.output.verbose_msg(["vcs_update", "vcs_git"], " Disk revisions matches")
            elif not failed:
                # test branch
                branch = self.__branch if self.__branch else self._env["GIT_DEFAULT_BRANCH"]

                api.output.verbose_msgf(["vcs_update", "vcs_git"], " Cached branch: {0}", cache['branch'])
                api.output.verbose_msgf(["vcs_update", "vcs_git"], " Requested branch: {0}", branch)

                if cache['branch'] != branch:
                    api.output.verbose_msg(["vcs_update", "vcs_git"],
                                           " Cache version of branch does not match.. verifying on disk..")
                    failed = True
                else:
                    api.output.verbose_msg(["vcs_update", "vcs_git"], " Disk branch matches")

        else:
            # there is no cache .. fallback to force logic
            api.output.verbose_msg(["vcs_update", "vcs_git"], " Data Cache does not exist.. doing force logic")
            failed = True

        if failed:
            return self.do_force_logic()

    def do_force_logic(self):
        ''' call for testing if what is one disk matches what the SConstruct says should be used

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        api.output.verbose_msg(["vcs_update", "vcs_git"], " Using force vcs logic.")
        # test for existence
        tmp = self.do_exist_logic()
        if tmp:
            api.output.verbose_msg(["vcs_update", "vcs_git"], " Existence checked failed")
            return tmp
        data = self.get_git_data()
        if data:
            if data['server'] != self.FullPath:
                api.output.verbose_msg(["vcs_update", "vcs_git"], " Disk checked failed")
                return 'Server on disk is different than the one requested for Parts "%s"\n On disk: %s\n requested: %s' % (
                    self._pobj.Alias, data['server'], self.FullPath)

            # check the revision is it was set
            if self.__revision and data['revision'] != self.__revision and data['short_revision'] != self.__revision:
                api.output.verbose_msg(["vcs_update", "vcs_git"], " Disk revision does not match")
                return 'revision on disk is different than the one requested for Parts "%s"\n On disk: %s\n requested: %s' % (
                    self._pobj.Alias, data['revision'], self.__revision)
            elif not self.__revision:
                # if branch was not set default branch to be checked
                branch = self.__branch if self.__branch else self._env["GIT_DEFAULT_BRANCH"]
                if branch and data['branch'] != "{0}...origin/{0}".format(branch) and branch not in data['tags']:
                    # check branch or tag
                    api.output.verbose_msg(["vcs_update", "vcs_git"], " Disk branch does not match")
                    return 'Branch on disk is different than the one requested for Parts "%s"\n On disk: %s\n requested: %s' % (
                        self._pobj.Alias, data['branch'], branch)

    def UpdateEnv(self):
        '''
        Update the with information about the current VCS object
        '''
        if git.gitpath is None:
            git.gitpath = _get_gitpath(self._env)

        if self._env['HOST_OS'] == 'win32':
            try:
                self._env['ENV']['GIT_SSH'] = os.environ['GIT_SSH']
            except KeyError:
                pass

        self._env['VCS'] = common.namespace(
            TYPE='git',
            CHECKOUT_DIR='$VCS_GIT_DIR',
            TOOL=git.gitpath,
            BRANCH=common.DelayVariable(lambda: self.get_git_data()['branch']),
            TAGS=common.DelayVariable(lambda: self.get_git_data()['tags']),
            SERVER_PATH=self.FullPath,
            MODIFIED=common.DelayVariable(lambda: self.get_git_data()['modified']),
            UNTRACKED=common.DelayVariable(lambda: self.get_git_data()['untracked']),
            REVISION=common.DelayVariable(lambda: self.get_git_data()['revision']),
            SHORT_REVISION=common.DelayVariable(lambda: self.get_git_data()['short_revision']),
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
            '__version__': 1.1,
            'type': 'git',
            'server': self.FullPath,
            'branch': self.__branch if self.__branch else "master",
            'revision': self.__revision,
            'completed': self._completed
        }

        datacache.StoreData(name=self._cache_filename, data=tmp, key='vcs')
        self._disk_data = None

    def is_modified(self):
        return self.get_git_data()['modified']

    def get_git_data(self):
        # get current state
        if self._disk_data is None:
            self._disk_data = GetGitData(self._env, self.CheckOutDir.abspath, patched=bool(self._patchfile))
        return self._disk_data

    @property
    def _cache_filename(self):
        return self._env['ALIAS']


class version_from_tag(object):
    def __init__(self, env):
        self.env = env

    def __call__(self, default, prefix='', regex=None, converter=None):
        '''
        util function to get version for tag value we are currently checkout on
        @parm default - the value to use if we are not on a tag or a tag that matches expected values
        @parm prefix - match prefix of tag value to be a match. Often cleaner than making a regex
        @parm regex - Optional expression to use for matching the Tag version value
        @parm converter - optional function that takes and environment object that will convert the version to a correct value
        '''
        # get tags
        try:
            tags = list(self.env["VCS"]["TAGS"])
        except KeyError:
            # this code was not checkout... fallback
            return default
        prefix = self.env.subst(prefix)
        # default set expression
        if regex:
            regex = re.compile(regex)
        else:
            # use default
            regex = re.compile(r'\d+\.\d+(?:\.\d+)*')

        if not tags:
            return default

        if not converter:
            def converter(ver, env): return ver

        versions = []
        for t in tags:
            result = regex.search(t)
            if result and t.startswith(prefix):
                ver = converter(result.group(), self.env)
                if ver:
                    versions.append(version.version(ver))
        versions.sort()
        return versions[-1]


def GetGitData(env, checkoutdir=None, patched=False):

    branch = None  # the branch we are one
    server = None  # the server with the data
    modified = False  # was this modifed locally
    untracked = False  # are there file that are not tracked
    revision = None  # what is our current hash
    short_revision = None  # short version of hash

    if checkoutdir is None:
        checkoutdir = env.AbsDir('$CHECK_OUT_DIR')

    if git.gitpath is None:
        git.gitpath = _get_gitpath(env)

    if not git.gitpath:
        api.output.warning_msg("Git was not found. Git state data cannot be retrieved.")

    if env['HOST_OS'] == 'win32':
        try:
            env['ENV']['GIT_SSH'] = os.environ['GIT_SSH']
        except KeyError:
            pass

    # get state on current branch on disk and if anything is modified or untracked
    ret, data = base.command_output('cd {1} && "{0}" status ${{GIT_STATUS_ARGS}} -s -b'.format(git.gitpath, checkoutdir))
    if not ret:
        data.replace('\r\n', '\n')
        # first line is the ## branch
        # check that we have this, else we have some serious error
        # and we will ignore the data
        if data.startswith("##"):
            lines = data.split('\n')
            branch = lines[0].split()[1]
            lines = lines[1:-1]  # remove first and last line
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
    if patched:
        ret, data = base.command_output('cd {1} && "{0}" tag ${{GIT_TAG_ARGS}} --points-at HEAD^'.format(git.gitpath, checkoutdir))
    else:
        ret, data = base.command_output('cd {1} && "{0}" tag ${{GIT_TAG_ARGS}} --points-at HEAD'.format(git.gitpath, checkoutdir))
    if not ret:
        data.replace('\r\n', '\n')
    tags = data.split('\n')[:-1]

    # get the revision hash for what is on disk
    ret, data = base.command_output('cd {1} && "{0}" rev-parse HEAD'.format(git.gitpath, checkoutdir))
    if not ret:
        revision = data.strip()
        short_revision = revision[:9]

    # get the server we will pull from
    ret, data = base.command_output('cd {1} && "{0}" remote -v'.format(git.gitpath, checkoutdir))
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
        'revision': revision,
        'short_revision': short_revision,
    }

    return ret


# add configuration variable needed for part
api.register.add_variable('GIT_SERVER', '', '')
api.register.add_variable('GIT_USER', '$PART_USER', '')
api.register.add_variable('VCS_GIT_DIR', '${CHECK_OUT_ROOT}/${PART_ALIAS}', '')
api.register.add_variable('GIT_DEFAULT_BRANCH', 'master', '')
api.register.add_bool_variable('GIT_IGNORE_UNTRACKED', False, 'Controls if we should care about untracked files when updating')
api.register.add_enum_variable('GIT_PROTOCOL', 'https', '', ['https', 'git'])

api.register.add_global_object('VcsGit', git)
api.register.add_global_object('ScmGit', git)
api.register.add_global_parts_object("GitVersionFromTag", version_from_tag, True)

SConsEnvironment.GitInfo = GetGitData
SConsEnvironment.GitVersionFromTag = version_from_tag
