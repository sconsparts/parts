


import os
import re

import parts.api as api
import parts.common as common
import parts.datacache as datacache
from parts.core import util
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

from .base import base, removeall


class svn(base):
    ''' This is the implementation of the vcs SVN logic'''

    __slots__ = [
        '__revision',
        '_disk_data',
        '_completed',
    ]
    svnpath = None  # the path to the svn program to run
    svnver = None  # the path the svnversion program
    connected_servers = []

    def __init__(self, repository, server=None, revision=None):
        '''Constructor call for the SVN object
        @param repository The repository or path from server under the server to get our data from
        @param server The server to connect to
        @param revision The optional revision to get. Defaults to latest revision
        '''
        self.__revision = revision
        self._disk_data = None
        self._completed = None
        if repository.endswith('/'):
            repository = repository[:-1]
        if server and server.endswith('/'):
            server = server[:-1]
        super(svn, self).__init__(repository, server)

    @base.Server.getter
    def Server(self):
        ''' svn property override to getting server data'''
        if self._server is not None:
            return self._server
        return self._env['SVN_SERVER']

    @property
    def Revision(self):
        rev_string = ''
        if self.__revision:
            rev_string = '@' + self.__revision + ' '
        else:
            try:
                rev_string = '@' + self._env['SVN_REVISION'] + ' '
            except KeyError:
                pass
            except TypeError:
                pass
        return rev_string

    def UpdateAction(self, out_dir):
        '''Returns the update Action for SVN

         in reality we may want to say update this area with a different version; the switch
         command is the more correct option in this case than the update command!
         '''

        clean_actions = [
            self._env.Action(lambda target, source, env: self.remove_unversioned(out_dir),
                             "Removing unversioned SVN files in {0}".format(out_dir)),
        ]
        for svnCommand in ('cleanup', '-R revert'):
            clean_actions.append(self._env.Action(
                '"{0}" {1} "{2}"'.format(svn.svnpath, svnCommand, out_dir),
                '{0} {1} "{2}"'.format('svn', svnCommand, out_dir)))

        # if the server is different we need to relocate
        update_path = self.FullPath

        if self.get_svn_data()['server'] != self.Server and self.get_svn_data()['server'] is not None:
            strval1 = '%s switch --relocate $SVN_FLAGS %s %s "%s"' % ('svn', self.get_svn_data()['server'], self.Server, out_dir)
            strval2 = '%s switch $SVN_FLAGS %s%s "%s"' % ('svn', update_path, self.Revision, out_dir)

            cmd1 = '"%s" switch --relocate $SVN_FLAGS %s %s "%s"' % (svn.svnpath,
                                                                     self.get_svn_data()['server'], self.Server, out_dir)
            cmd2 = '"%s" switch $SVN_FLAGS %s%s "%s"' % (svn.svnpath, update_path, self.Revision, out_dir)
            ret = [self._env.Action(cmd1, strval1), self._env.Action(cmd2, strval2)]
            if self._env.GetOption('vcs_clean') == True:
                ret = clean_actions + ret
        # this happens when we switch repro types ( should do better fix for this..)
        # what happens is that there is no SVN info to get and a possible directory
        elif self.get_svn_data()['server'] is None:
            if self._env.GetOption('vcs_clean') == True or self._env.GetOption('vcs_retry') == True:
                ret = [self._env.Action(lambda target, source, env: removeall(
                    out_dir), "Cleaning up checkout area for {0}".format(out_dir))] + self.CheckOutAction(out_dir)
            else:
                api.platforms.output.error_msg(
                    'Directory "{0}" already exists with no .svn directory. Manually remove directory or update with --scm-retry or --scm-clean'.format(
                        out_dir),
                    show_stack=False)
        else:
            strval = '%s switch $SVN_FLAGS %s%s "%s"' % ('svn', update_path, self.Revision, out_dir)
            cmd = '"%s" switch $SVN_FLAGS %s%s "%s"' % (svn.svnpath, update_path, self.Revision, out_dir)
            ret = [self._env.Action(cmd, strval)]
            if self._env.GetOption('vcs_clean') == True:
                ret = clean_actions + ret

        return ret

    def CheckOutAction(self, out_dir):
        ''' returns the action to do the checkout'''
        strval = '%s checkout $SVN_FLAGS %s%s "%s"' % ('svn', self.FullPath, self.Revision, out_dir)
        cmd = '"%s" checkout $SVN_FLAGS %s%s "%s"' % (svn.svnpath, self.FullPath, self.Revision, out_dir)
        return [self._env.Action(cmd, strval)]

    def remove_unversioned(self, path):
        unver_re = re.compile(r'^ ?[\?ID] *[1-9 ]*[a-zA-Z]* +(.*)')
        lines = self.command_output('svn status --no-ignore -v {0}'.format(path))[1].split('\n')
        for i in lines:
            tmp = unver_re.match(i)
            if tmp:
                removeall(tmp.group(1))

    def clean_step(self, out_dir):
        ''' since svn tends to checkout the .svn meta data area as readonly
        it turns out that we can't clean the checked out code correctly as
        python will not clean the files that are readonly. This makes it so
        all the data is writable so we can do the delete actions
        '''

        import stat
        # small Hack to turn off SVN read only access so we can delete
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
        api.output.verbose_msg(["vcs_update", "vcs_svn"], " Doing existence check")
        if self.PartFileExists and os.path.exists(os.path.join(self.CheckOutDir.abspath, '.svn')):
            return None
        api.output.verbose_msg(["vcs_update", "vcs_svn"], " Existence check failed")
        return "%s needs to be updated on disk" % self._pobj.Alias

    def do_check_logic(self):
        ''' call for checking if what we have in the data cache is matching the current checkout request
        in the SConstruct match up

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        api.output.verbose_msg(["vcs_update", "vcs_svn"], " Using scm-logic: check.")
        # test for existence
        tmp = self.do_exist_logic()
        if tmp:
            return tmp
        # get data cache and see if our paths match
        cache = datacache.GetCache(name=self._env['ALIAS'], key='vcs')
        if cache:
            api.output.verbose_msg(["vcs_update", "vcs_svn"], " Cached server: %s" % (cache['server']))
            api.output.verbose_msg(["vcs_update", "vcs_svn"], " Requested Server: %s" % (self.FullPath))
            if cache['server'] != self.FullPath:
                api.output.verbose_msg(["vcs_update", "vcs_svn"], " Cache version of server does not match.. verifing on disk..")
                # hard check to verify it is really bad
                data = self.get_svn_data()
                if data:
                    if data['url'] != self.FullPath:
                        api.output.verbose_msg(["vcs_update", "vcs_svn"], " Disk version does not match")
                        return 'Server on disk is different than the one requested for Parts "%s\n On disk: %s\n requested: %s"' % (
                            self._pobj.Alias, data['url'], self.FullPath)
                    else:
                        api.output.verbose_msg(["vcs_update", "vcs_svn"], " Disk version matches")
                else:
                    api.output.verbose_msg(["vcs_update", "vcs_svn"], " Could not query disk version for information!")
                    return 'Disk copy seems bad... updating'
        else:
            api.output.verbose_msg(["vcs_update", "vcs_svn"], " Data Cache does not exist.. doing force logic")
            return self.do_force_logic()

    def do_force_logic(self):
        ''' call for testing if what is one disk matches what the SConstruct says should be used

        returns None if it passes, returns a string to possible print tell why it failed
        '''
        api.output.verbose_msg(["vcs_update", "vcs_svn"], " Using force vcs logic.")
        # test for existence
        tmp = self.do_exist_logic()
        if tmp:
            api.output.verbose_msg(["vcs_update", "vcs_svn"], " Existence checked failed")
            return tmp
        data = self.get_svn_data()
        if data:
            if data['url'] != self.FullPath:
                api.output.verbose_msg(["vcs_update", "vcs_svn"], " Disk checked failed")
                return 'Server on disk is different than the one requested for Parts "%s\n On disk: %s\n requested: %s"' % (
                    self._pobj.Alias, data['url'], self.FullPath)
            else:
                return None

    def UpdateEnv(self):
        '''
        Update the with information about the current VCS object
        '''
        if svn.svnpath is None:
            tmp = self._env.WhereIs('svn')
            if not tmp:
                tmp = self._env.WhereIs('svn', os.environ['PATH'])
            if not tmp:
                api.output.error_msg("Could find svn on the system!", show_stack=False)
            svn.svnpath = tmp
        try:
            # useful for linux boxes
            self._env['ENV']['DBUS_SESSION_BUS_ADDRESS'] = os.environ['DBUS_SESSION_BUS_ADDRESS']
        except KeyError:
            pass

        self._env['VCS'] = common.namespace(
            TYPE='svn',
            CHECKOUT_DIR='$VCS_SVN_DIR',
            TOOL=svn.svnpath,
            REVISION=common.DelayVariable(lambda: self.get_svn_data()['revision']),
            REVISION_LOW=common.DelayVariable(lambda: self.get_svn_data()['revision_low']),
            SERVER_PATH=self.FullPath,
            MODIFIED=common.DelayVariable(lambda: self.get_svn_data()['modified']),
            PARTIAL=common.DelayVariable(lambda: self.get_svn_data()['partial']),
            SWITCHED=common.DelayVariable(lambda: self.get_svn_data()['switched']),
            FLAGS=self._env['SVN_FLAGS']
        )

    def ProcessResult(self, result):
        ''' Handle SVN logic we want need to handle

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
            'type': 'svn',
            'server': self.FullPath,
            'completed': self._completed
        }

        datacache.StoreData(name=self._cache_filename, data=tmp, key='vcs')
        self._disk_data = None

    def is_modified(self):
        return self.get_svn_data()['modified']

    def get_svn_data(self):
        # get current state
        if self._disk_data is None:
            self._disk_data = GetSvnData(self._env, self.CheckOutDir.abspath)
        return self._disk_data

    @property
    def _cache_filename(self):
        return self._env['ALIAS']


def GetSvnData(env, checkoutdir=None):

    server = None
    url = None
    modified = False
    switched = False
    partial = False
    rev_low = None
    rev_high = None

    if checkoutdir is None:
        checkoutdir = env.AbsDir('.')

    if svn.svnver is None:
        svn.svnver = env.WhereIs('svnversion', os.environ['PATH'])
    if svn.svnpath is None:
        svn.svnpath = env.WhereIs('svn', os.environ['PATH'])

    ret, data = base.command_output('"{0}" {1}'.format(svn.svnver, checkoutdir))
    # this is a quick check to see if the current directory may be in bad state
    # but not unversioned. Given that we try to the directory above us, till we get an unversioned
    # value
    while not ret and not data.startswith('Unversioned') and data[0] not in '0123456789':
        checkoutdir = os.path.split(checkoutdir)[0]
        if checkoutdir == '':
            break
        ret, data = base.command_output('"{0}" {1}'.format(svn.svnver, checkoutdir))

    if not ret and data[0] in '0123456789':
        data = data.strip('\n\r\t ')
        if data == 'exported':
            pass
        else:
            tmp = data.split(':')
            if len(tmp) == 2:
                rev_low = int(tmp[0])
                i = tmp[1]
            else:
                i = tmp[0]
                indx = 0
                if 'M' in i:
                    modified = True
                    indx -= 1
                if 'S' in i:
                    switched = True
                    indx -= 1
                if 'P' in i:
                    partial = True
                if indx < 0:
                    rev_high = int(i[:indx])
                else:
                    rev_high = int(i)

    # get the path
    ret, data = base.command_output('"{0}" info {1}'.format(svn.svnpath, checkoutdir))
    if not ret:
        data = data.replace('\r\n', '\n')
        tmp = data.split('\n')
        for i in tmp:
            if i.startswith('URL: '):
                url = i[5:]
            elif i.startswith('Repository Root: '):
                server = i[len('Repository Root: '):]

    ret = {
        'revision': rev_high,
        'revision_low': rev_low,
        'modified': modified,
        'switched': switched,
        'partial': partial,
        'url': url,
        'server': server
    }
    return ret


# add configuartion varaible needed for part
api.register.add_variable('SVN_SERVER', '', 'Value of SVN server to use')
api.register.add_list_variable('SVN_FLAGS', ['--non-interactive'], 'Flags to use for the svn call')
#api.register.add_variable('SVN_REVISION',None,'Value of SVN revision to checkout, None mean latest' )
api.register.add_variable('VCS_SVN_DIR', '${CHECK_OUT_ROOT}/${PART_ALIAS}', 'Full path used for any given checked out item')

api.register.add_global_object('VcsSvn', svn)
api.register.add_global_object('ScmSvn', svn)

SConsEnvironment.SvnInfo = GetSvnData
