import os
import types

import setup
import testrun
import conditions
import testers
import host


class Test(object):
    """Defines a test.
    A test contains a list of test runs objects,
    information about the test, such as name, discription,
    can the test run in threaded with other tests and a
    setup/clean up object to help control the environment 
    the test will run in
    """
    __slots__=[
               "__run_serial",
               "__summary",
               "__name",
               "__setup",
               "__test_runs",
               "__test_dir",
               "__test_file",
               "__test_root",
               "__run_dir",
               "__result",
               "__conditions",
               "__env",
               ]
    
    def __init__(self,name,test_dir,test_file,run_root,test_root):
        # traits
        self.__run_serial=False
        self.__summary=''
        self.__name=name # name of the test

        ##internal data
        # the different test runs
        self.__test_runs=[] 
        # this is the location of the test file
        self.__test_dir=test_dir
        #this is the name of the test file
        self.__test_file=test_file
        #this is the directory we scanned to find this test
        self.__test_root=test_root
        #this is the directory we will run the test in
        self.__run_dir = os.path.normpath(os.path.join(run_root, name))
        #this is the result of the test ( did it pass, fail, etc...)
        self.__result=None

        # property objects
        self.__setup = setup.Setup(self)
        self.__conditions=conditions.Conditions()
        # make a copy of the environment so we can modify it without issue
        self.__env=os.environ.copy()
        #add some default values
        self.__env['GTEST_TEST_ROOT_DIR']=self.__test_root
        self.__env['GTEST_TEST_DIR']=self.__test_dir
        self.__env['GTEST_RUN_DIR']=self.__run_dir

        
# public properties
    @property
    def Name(self):
        return self.__name

    @Name.setter
    def Name(self,val):
        self.__name=val

    @property
    def Summary(self):
        return self.__summary

    @Summary.setter
    def Summary(self,val):
        self.__summary=val

    @property
    def RunSerial(self):
        return self.__run_serial

    @RunSerial.setter
    def RunSerial(self,val):
        self.__run_serial=val

    @property
    def Setup(self):
        return self.__setup

    def SkipIf(self,*lst):
        return self.__conditions._AddConditionIf(lst)

    def SkipUnless(self,*lst):
        return self.__conditions._AddConditionUnless(lst)

    @property
    def TestDirectory(self):
        return self.__test_dir

    @property
    def TestFile(self):
        return self.__test_file

    @property
    def TestRoot(self):
        return self.__test_root

    @property
    def RunDirectory(self):
        return self.__run_dir

    @property
    def Env(self):
        return self.__env


# public methods 
    def AddTestRun(self, name='general', displaystr=None):
        tmp = testrun.TestRun(self, "%s-%s" % (len(self._TestRuns), name), displaystr)
        self._TestRuns.append(tmp)
        return tmp

    
#internal stuff
    @property
    def _Result(self):
        if self.__result is None:
            for tr in self.__test_runs:
                if self.__result < tr._Result:
                    self.__result = tr._Result
            # result is None and we have no tests to run
            if self.__result is None and len(self.__test_runs)==0:
                return testers.ResultType.Passed
        return self.__result

    def _SetResult(self,val):
        self.__result=val

    @property
    def _TestRuns(self):
        return self.__test_runs

    @property
    def _Conditions(self):
        return self.__conditions

def AddTestRunSet(func,name=None):
    if name is None:
        name=func.__name__
    method=types.MethodType(func,None,Test)
    setattr(Test,name,method)
    host.WriteVerbose("testext",'Added TestRun extension function "{0}"'.format(name))
