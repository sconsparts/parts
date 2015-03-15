import subprocess
import os,sys
import platform
import stat

import glb

class Condition(object):
    def __init__(self, testfunc, reason, pass_value):
        self.__func = testfunc
        self.__msg = reason
        self.__pass_value = pass_value

    def __nonzero__(self):
        return self.Pass()

    def Pass(self):
        return self.__pass_value == self.__func()

    @property
    def Message(self):
        return self.__msg


class ConditionFactory(object):
    def __call__(self,function,reason,pass_value=True):
        return self.Condition(function,reason,pass_value)

    def Condition(self,function,reason,pass_value=True):
        '''This is a general function for any condition testing
        it takes a a function that will return true or false
        a message to report why this condition failed ( and as such we skipped the test)
        optional value to control if the return value of False should be used as a failure of
        the condition. defaults to True.. ie False is failure and True is passing.
        '''

        ret=Condition(function,reason,pass_value)
        return ret

    def HasRegKey(self,root,keys,msg):
        return self.Condition(
                       lambda : _has_regkey(root,keys),
                       msg,
                       True
                       )

    def RegistryKeyEqual(self,key):
        pass

    def RunCommand(self,command,msg,pass_value=0,env=None,shell=False):
        return self.Condition(
                       lambda :subprocess.call(command,shell=False),
                       msg,
                       pass_value
                       )

    def HasProgram(self,program,msg,pass_value=True,path=None):
        return self.Condition(
                       lambda :_has_program(program,path),
                       msg,
                       pass_value
                       )

    def IsPlatform(self,*lst):
        return self.Condition(
                       lambda :sys.platform.lower() in lst or platform.system().lower() in lst or os.name.lower() in lst,
                       'Platform must be one of {0}, reported value was "{1}" or "{2}"'.format(
                                                                                              lst,
                                                                                              platform.system().lower(),
                                                                                              os.name
                                                                                              ),
                       True
                       )

    def IsNotPlatform(self,*lst):
        return self.Condition(
                       lambda :sys.platform.lower() in lst or platform.system().lower() in lst or os.name.lower() in lst,
                       'Platform must not be one of {0}, reported value was "{1}" or "{2}"'.format(
                                                                                                  lst,
                                                                                                  platform.system().lower(),
                                                                                                  os.name
                                                                                                  ),
                       False
                       )



class Conditions(object):
    """description of class"""
    def __init__(self):
        self.__condition_if=[]
        self.__condition_unless=[]

    def _AddConditionIf(self,conditions=[]):
        self.__condition_if.extend(conditions)

    def _AddConditionUnless(self,conditions=[]):
        self.__condition_unless.extend(conditions)

    # internal functions properties
    @property
    def _Passed(self):
        '''Test all the conditions to see if they all pass
        return True if we have a failure and should skip
        '''
        # loop on skipunless
        for cond in self.__condition_unless:
            if not cond:
                # we had a failure
                self.__reason=cond.Message
                return False
        # loop on skipif
        for cond in self.__condition_if:
            if cond:
                # we had a failure
                self.__reason=cond.Message
                return False

        return True

    @property
    def _Reason(self):
        return self.__reason

    # internal functions
    def _Empty(self):
        '''Removes all condtions tests that have been defined'''
        self.__conditions=[]


# some util functions
def _has_program(program,path=None):
    return _where_is(program,path)!=None

def _where_is(program,path=None):
    #get the path we need to check
    if path is None:
        try:
            path = os.environ['PATH'].split(os.pathsep )
        except KeyError:
            # no path set?
            #well there is nothing to find.
            return None
    try:
        pathext = os.environ['PATHEXT'].split(os.pathsep )
    except KeyError:
        pathext = [""]

    for dir in path:
        f = os.path.join(dir, program)
        if pathext:
            for ext in pathext:
                fext = f + ext
                if os.path.isfile(fext):
                    st = os.stat(fext)
                    if stat.S_IMODE(st[stat.ST_MODE]) & stat.S_IXUSR:
                        return os.path.normpath(fext)

    return None

if sys.platform == 'win32':
    from  _winreg import *

    glb.Locals['HKEY_CLASSES_ROOT']=HKEY_CLASSES_ROOT
    glb.Locals['HKEY_CURRENT_USER']=HKEY_CURRENT_USER
    glb.Locals['HKEY_LOCAL_MACHINE']=HKEY_LOCAL_MACHINE
    glb.Locals['HKEY_USERS']=HKEY_USERS
    glb.Locals['HKEY_CURRENT_CONFIG']=HKEY_CURRENT_CONFIG

    def _has_regkey(root,keys):

        try:
            for fullkey in keys:
                path,key = fullkey.rsplit('\\',1)
                # get path container
                try:
                    # normal case is that we want to get a key
                    with OpenKey(root,path) as rpath:
                        #get key value
                        QueryValueEx(rpath,key)
                    return True
                except WindowsError,e:
                    try:
                        # maybe this was just checking for a path
                        with OpenKey(root,fullkey) as rpath:
                            pass
                        return True
                    except WindowsError,e:
                        pass

        except WindowsError,e:
            pass

        return False

    def reg_key_equal(key,value):
        pass

else:
    glb.Locals['HKEY_CLASSES_ROOT']=1
    glb.Locals['HKEY_CURRENT_USER']=2
    glb.Locals['HKEY_LOCAL_MACHINE']=3
    glb.Locals['HKEY_USERS']=4
    glb.Locals['HKEY_CURRENT_CONFIG']=5

    def _has_regkey(root,key):
        return False


    def reg_key_equal(key,value):
        return False
