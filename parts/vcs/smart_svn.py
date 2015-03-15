from .. import common
from .. import datacache
from .. import api
from .. import version
from .. import target_type

from .base import normalize_url

import SCons.Script
import svn

import os

class smart_svn(svn.svn):
    __slots__=[
            '_vars',
            '_branch_info',
            '_stored_version',
            '_stored_uid',
            '_stored_uid_path',
        ]
    def __init__(self,
                component_name, # this is the name of the component to use when looking it up
                component_type, # the type of component this is.
                stable_version, # The version that is stable in the product ie "1.2.3"
                sub_dir='', # directory under the location we will generate to add too

                server=None,
                revision=None,
                **kw
             ):

        self._vars={}
        self._vars.update(kw)
        self._vars['NAME']=component_name
        self._vars['COMPONENT_TYPE']=component_type
        self._vars['STABLE_VERSION']=version.version(stable_version)

        self._vars['SUB_DIR']=sub_dir
        self._vars['BRANCH_PATH']=self.find_best_branch
        self._branch_info={}
        self._stored_version=None
        self._stored_uid=''
        self._stored_uid_path=''
        super(smart_svn, self).__init__('',server,revision)

    def UpdateEnv(self):
        '''
        Override the base svn function to allow us to set certain values in the correct order
        to prevent issue with mapping repository information provided by the user
        '''
        if svn.svn.svnpath is None:
            #svn.svnpath=self._env.WhereIs('svn')
            svn.svn.svnpath=self._env.WhereIs('svn',os.environ['PATH'])
            if svn.svn.svnpath is None:
                svn.svn.svnpath=self._env.WhereIs('svn',os.environ['PATH'])

        # get cache states
        cache=datacache.GetCache(name=self._cache_filename,key='vcs')

        if cache:
            if cache.get('type') == 'smartsvn':
                self._branch_info=cache['branch_info']
                self._stored_version=version.version(cache['stable_version'])
                self._completed=cache['completed']
                self._stored_uid=cache['user']
                self._stored_uid_path=cache['uid_path']

        # get the different types
        tmp= common.namespace(**self._env.get('SVN_TYPE_MAP',{}))
        self._vars['TYPE_MAP']=tmp
        try:
            self._vars['COMPONENT_TYPE_PATH']=tmp[self._vars['COMPONENT_TYPE']]
        except KeyError:
            api.output.error_msgf("{0} is not a known component type",self._vars['COMPONENT_TYPE'])

        # get the different branches
        tmp= common.namespace(**self._env.get('SVN_BRANCH_MAP',{}))
        self._vars['BRANCH_MAP']=tmp

        # stuff that is useful if the user has some sort of user ID branch
        self._vars['USER'] = '${0}_USER'.format(self._vars['NAME'].upper())
        try:
            self._env['{0}_USER'.format(self._vars['NAME'].upper())]
        except KeyError:
            self._env['{0}_USER'.format(self._vars['NAME'].upper())] = '$PART_USER'

        self._vars['UID_PATH'] = '${0}_UID_PATH'.format(self._vars['NAME'].upper())
        try:
            self._env['{0}_UID_PATH'.format(self._vars['NAME'].upper())]
        except KeyError:
            self._env['{0}_UID_PATH'.format(self._vars['NAME'].upper())] = '$UID_PATH'

        #setup a few more values we will need to fill in the different pieces
        repo=self._env['SVN_REPOSITORY']

        # we don't set the server path
        self._env['VCS']=common.namespace(
                TYPE='smartsvn',
                CHECKOUT_DIR='$VCS_SMART_SVN_DIR',
                TOOL=svn.svn.svnpath,
                FLAGS=self._env['SVN_FLAGS'],
                REPOSITORY=repo,
                SERVER=self.Server,
                REVISION=common.DelayVariable(lambda : self.get_svn_data()['revision']),
                REVISION_LOW=common.DelayVariable(lambda : self.get_svn_data()['revision_low']),
                MODIFIED=common.DelayVariable(lambda :self.get_svn_data()['modified']),
                PARTIAL=common.DelayVariable(lambda :self.get_svn_data()['partial']),
                SWITCHED=common.DelayVariable(lambda :self.get_svn_data()['switched']),
                )

        self._env['VCS'].update(**self._vars)

        # calling this will require some work to be done
        self._env['VCS']['SERVER_PATH']=self.FullPath



    @property
    def Repository(self):
        '''returns the value of the server

        Subclasses may add to this logic as they might want to define other values based on custom logic.
        '''
        if self._repository == '':
            self._repository=self.find_best_branch(self._env.GetOption('vcs_logic')=='force')
        return self._repository

    def find_best_branch(self,force=False):
        '''This function will try to get the correct repository value to use
        for a checkout. For a given Branch it will try to see if a given location exists
        in SVN, and if it does use it, else if will fallback to different location or error out
        if nothing is found.
        '''
        # get branch we want
        branch=self.GetBranchType()
        api.output.verbose_msgf("smart_svn","Finding information for branch {0}",branch)
        ##if force is false we will try to see if we can use a cache
        if force == False:
            try:
                api.output.verbose_msgf("smart_svn","looking for stored state of {0}",self._env.subst('${VCS.NAME}'))
                if self._stored_version!=self._vars['STABLE_VERSION']:
                    api.output.verbose_msgf("smart_svn","Stable version does not match: {0} != {1}", self._stored_version, self._vars['STABLE_VERSION'])
                elif self._stored_uid!=self._env.subst('${VCS.USER}'):
                    api.output.verbose_msg("smart_svn","user (UID) does not match {0}!={1}".format(self._stored_uid,self._env.subst('${VCS.USER}')))
                elif self._stored_uid_path!=self._env.subst('${VCS.UID_PATH}'):
                    api.output.verbose_msg("smart_svn","uid path does not match {0}!={1}".format(self._stored_uid_path,self._env.subst('${VCS.UID_PATH}')))
                elif not self._completed:
                    api.output.verbose_msg("smart_svn","Operation failed to complete last time, relooking up")
                else:
                    tmp=self._branch_info[branch]
                    # we may want to retry if the branchs don't match, in case the reason for fallback
                    # have been corrected. Think about adding this.
                    api.output.verbose_msg("smart_svn","Found state",tmp)
                    return tmp # returns (found branch,path)
            except KeyError:
                api.output.verbose_msgf("smart_svn","No state was found: {0}",self._env.subst('${VCS.NAME}'))

        api.output.verbose_msgf("smart_svn", "Getting state from repository: {0}",self._env.subst('${VCS.NAME}'))

        ret=self.find_match_for_branch(branch)
        if ret is None:

            api.output.error_msgf(
                'Could not find {0} branch "{1}" in svn\n looked in {2}',
                self._vars['NAME'],branch,self._env.subst(self._vars['BRANCH_MAP'][branch]),
                show_stack=False
                )
        ret = normalize_url(ret)
        self._branch_info[branch]=ret
        return ret

    def find_match_for_branch(self,branch):
        '''This will return the path to requested branch else None

        @param branch The branch type we want to get a path for
        '''

        # get a list of paths we have to check
        try:
            brch_lst = common.make_list(self._vars['BRANCH_MAP'][branch])
        except KeyError:
            err_str='''Error: Invalid option for build branch: "{0}" Usage:
 --build-branch=<branch>|default:<branch>|<Component name>:<branch>,...

 <branch and default:<branch> set the default branch value for a given Part
 <part ref>:branch set the branch for a given Part(s) referred to by <part ref>
 <branch> can be {1}
 <component name> which is the value of the component_name argument in the VcsSmartSvn()'''.format(branch,self._vars['BRANCH_MAP'].keys())
            api.output.error_msg(err_str,show_stack=False)
        # check each path till we get a hit
        for path in brch_lst:
            self._env['VCS']['BRANCH_TYPE_PATH']=path
            # resolve any variables
            repo_path=self._env.subst("${VCS.REPOSITORY}").replace('\\','/')
            svn_path=self._env.subst("{0}/{1}".format(self.Server,repo_path)).replace('\\','/')
            #test path
            api.output.verbose_msg("smart_svn",'Testing path "%s"'%svn_path)

            retcode,text=self.command_output('"{0}" ls --non-interactive {1}'.format(svn.svn.svnpath,svn_path))
            api.output.verbose_msg(["smart_svn_hidden","smart_svn"],text)
            if not retcode:
                api.output.verbose_msg("smart_svn","Path was found")
                break
            api.output.verbose_msg("smart_svn","Path was not found")
        else:
            repo_path=None
        return repo_path

    def GetBranchType(self):
        # backward compatible stuff
        branch=self._env.get("{0}_BRANCH".format(self._env['VCS']['NAME']),self._env.get('BUILD_BRANCH','stable'))
        #new stuff
        value=self._env.GetOption('build_branch')

        for k,v in value.iteritems():
            t=target_type.target_type(k)
            # we ignore version.. as we don't know it technically.
            if t.Alias == self._env['VCS']['NAME'] or t.Name == self._env['VCS']['NAME']:
                return v
        else:
            # the else is what we want to default to.. this if statement is for compatiblity
            if branch != '':
                return branch
            else:
                return value['default']

    def PostProcess(self):
        ''' This function is called when the system is done with all the update checks and disk updates
        This allows the object to update an data it needs on disk, or in the environment. This is always called.
        '''
        if self._completed is None:
            self._completed=True
        #Setup and store vcs data cache logic
        tmp={
        '__version__':1.0,
        'type':'smartsvn',
        'server':self.FullPath,
        'completed':self._completed,
        'branch_info':self._branch_info,
        'stable_version':str(self._vars['STABLE_VERSION']),
        'user':self._env.subst('${VCS.USER}'),
        'uid_path':self._env.subst('${VCS.UID_PATH}')
        }

        datacache.StoreData(name=self._cache_filename,data=tmp,key='vcs')

api.register.add_global_object('VcsSmartSvn',smart_svn)
api.register.add_variable('VCS_SMART_SVN_DIR','${CHECK_OUT_ROOT}/${VCS.NAME}${VCS.STABLE_VERSION}','Full path used for any given checked out item')
api.register.add_variable('UID_PATH','<unknown>','')
from .. import glb
from optparse import OptionValueError
def opt_branch(option, opt, value, parser):

    tmp=value.lower()

    fvalue={'default':'stable'}
    tmp=value.split(',')
    for t in tmp:

        try:
            # need better logic to validate arguments.. but this will do for now
            k,v=t.rsplit(':',1)
        except:
            fvalue['default']=t
            continue

        k=k.lower()
        v=v.lower()

        fvalue[k]=v


    parser.values.build_branch=fvalue

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment
api.register.add_variable('BUILD_BRANCH',"","")

SCons.Script.AddOption("--build-branch","--bb",
            dest='build_branch',
            default={'default':'stable'},
            callback=opt_branch,
            type='string',
            action='callback',
            help='Controls which Branch to used by smart SVN logic.')
