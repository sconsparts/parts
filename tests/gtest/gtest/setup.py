import subprocess
import os
import shutil
import exceptions
import types
import string # for Template

from streamwriter import StreamWriter, PipeRedirector
import host
import common.pathutils

# the Error object for some setup failure
class Error(exceptions.Exception):
    def __init__(self,msg):
        self.__msg=msg
    def __str__(self):
        return self.__msg

#base class for any Setup task extension
# contains basic API that maybe useful in defining a given task.
class SetupTask(object):
    def __init__(self,taskname):
        self.__taskname=taskname
        self.__test=None
        self.cnt=0
    # basic properties values we need
    @property
    def TaskName(self):
        #name of the task
        return self.__taskname
    
    @TaskName.setter
    def TaskName(self,val):
        #name of the task
        self.__taskname=val

    @property
    def SandBoxDir(self):
        #directory we run the test in
        return self.__test.RunDirectory
    
    @property
    def TestRootDir(self):
        #the directory location given to scan for files for all the tests
        return self.__test.TestRoot

    @property
    def TestFileDir(self):
        #the directory the test file was defined in
        return self.__test.TestDirectory

    # useful util functions
    def RunCommand(self,cmd): 

        #create a StreamWriter which will write out the stream data of the run to sorted files
        output=StreamWriter(os.path.join(self.__test.RunDirectory,"_setup_tmp_{0}_{1}".format(self.TaskName.replace(" ","_"),self.cnt)),cmd)
        self.cnt+=1
        # the command line we will run. We add the RunDirectory to the start of the command 
        #to avoid having to deal with cwddir() issues
        command_line="cd {0} && {1}".format(self.__test.RunDirectory,cmd)
        # subsitute the value of the string via the template engine
        # as this provide a safe cross platform $subst model.
        template = string.Template(command_line)
        command_line=template.substitute(self.__test.Env)

        proc = subprocess.Popen(
            command_line,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.__test.Env)

        # get the output stream from the process we created and redirect to files
        stdout = PipeRedirector(proc.stdout, output.WriteStdOut)
        stderr = PipeRedirector(proc.stderr, output.WriteStdErr)
        
        proc.wait()
        
        output.Close()
        
        # clean up redirectory objects for this run
        stdout.close()
        stderr.close()

        return proc.returncode

    def Copy(self,source,target=None):
        source,target=self._copy_setup(source,target)
        host.WriteVerbose("setup","Copying {0} to {1}".format(source,target))
        if os.path.isfile(source):
            shutil.copy2(source,target)
        else:
            common.pathutils.copy_tree(source,target)
        
    def _copy_setup(self,source,target=None):
        # check to see if this is absolute path or not
        if not os.path.isabs(source):
            #if not we assume that the directory is based on our
            # Sandbox directory
            source=os.path.join(self.TestFileDir,source)
        if target:
            if not os.path.isabs(target):
                # this is an error
                pass
            target=os.path.join(self.SandBoxDir,target)
        else:
            # given that target is None we assume that we want to copy it
            # the sandbox directory with the same name as the source
            target=os.path.join(self.SandBoxDir,os.path.basename(source))
        return (source,target)

    def CopyDirectory(self,source,target=None):
        shutil.copytree(self._copy_setup(source,target))

    def CopyFile(self,source,target=None):
        shutil.copy2(self._copy_setup(source,target))

    def _bind(self,test):
        '''
        Allow us to bind the Test information with the setup task
        This is done before we try to execute the setup logic
        '''
        self.__test=test

    def cleanup(self):
        pass

    @property
    def Env(self):
        return self.__test.Env

_setup_spaces={}
class _setup__metaclass__(type):
        def __call__(cls,*lst,**kw):
            inst=type.__call__(cls,*lst,**kw)
            for k,v in _setup_spaces.iteritems():
                setattr(inst,k,v(inst))
            return inst

class Setup(object):
    __metaclass__=_setup__metaclass__

    def __init__(self,test):
        self.__setup_tasks=[]
        self.__test=test
        self.__reason=None
    
    def _add_task(self,task):
        # bind the setup task with the test object so it 
        # can get information about certain locations
        task._bind(self.__test)
        self.__setup_tasks.append(task)

    def _get_tasks(self):
        return self.__setup_tasks

    def _do_setup(self):
        tasks=self._get_tasks()
        try:
            for t in tasks:
                t.setup()
        except Error, e:
            self.__reason=str(e)
            raise e

    def _do_cleanup(self):
        tasks=self.__test.Setup._get_tasks()
        try:
            for t in tasks:
                t.cleanup()
        except Error, e:
            self.__reason=str(e)
            raise e
    @property
    def _Reason(self):
        if not self.__reason:
            return "Setup has no issues"
        return self.__reason
    
    @_Reason.setter
    def _Reason(self, value):
        self.__reason = value

    @property
    def _Failed(self):
        return self.__reason is not None

class ns_type(object):
    def __init__(self,obj):
        self._parent=obj    
    
    def _add_task(self,task):
        self._parent._add_task(task)

    
def AddSetupTask(task,name=None,ns=None):
    # helper function
    def wrapper(self,*lst,**kw):
            self._add_task(task(*lst,**kw))
    ## todo add check to make sure this is a setuptask type
    
    #get name of task if user did not provide a value
    if name is None:
        name=task.__name__

    if ns is None:
        host.WriteVerbose("setupext","Adding setup extension named: {0}".format(name))
        method=types.MethodType(wrapper,None,Setup)
        setattr(Setup,name,method)
    else:
        # see if we have this namespace defined already
        nsobj=_setup_spaces.get(ns)
        if nsobj is None:
            #create the ns object
            nsobj=type(ns,(ns_type,),{})
            #copy on class type as defined for given name
            _setup_spaces[ns]=nsobj
        #add new method to namespace object
        x=types.MethodType(wrapper,None,nsobj)
        setattr(nsobj,name,x)
        host.WriteVerbose("setupext","Adding setup extension named: {0} to namespace: {1}".format(name,ns))