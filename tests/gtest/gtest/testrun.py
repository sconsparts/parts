import os

import events
import host
import testers.equal

class DelayedEventMapper(object):
    '''
    This class provides the base interface for creating predefined event mappings for a
    defined concept
    '''
    __slots__ = ['__addevent']

    def __init__(self):
        self.__addevent={}

    def _BindEvents(self):
        for event, callback in self.__addevent.itervalues():
            event += callback

    def _RegisterEvent(self, key, event, callback):
        self.__addevent[key] = (event, callback)

    def _GetRegisterEvent(self, key):
        try:
            return self.__addevent[key]
        except KeyError:
            return None

class RegisterCheckerMixin(object):
    def _RegisterChecker(self, key, checkerCallback, event=None):
        try:
            checker = checkerCallback()
            if event is None:
                event = self._TestRun.RunFinished
            if checker:
                self._RegisterEvent(key, event, checker)
            else:
                host.WriteError('Invalid type')
        except BaseException, err:
            import traceback
            host.WriteError('Exception occurred: %s' % traceback.format_exc())

class BaseTestRunItem(RegisterCheckerMixin, object):
    counter = 0

    def __init__(self, testrun):
        self.__testrun = testrun
        self.__counter = BaseTestRunItem.counter
        BaseTestRunItem.counter += 1

    def _RegisterEvent(self, key, event, callback):
        self.__testrun._RegisterEvent('%s-%s' % (key, self.__counter), event, callback)

    def _GetRegisterEvent(self, key):
        return self.__testrun._GetRegisterEvent('%s-%s' % (key, self.__counter))

    @property
    def _TestRun(self):
        return self.__testrun

class Streams(BaseTestRunItem):
    def __init__(self,testrun):
        super(Streams, self).__init__(testrun)

    def __defineProperties__(properties):
        def createStreamProperty(name, event, testValue):
            def getter(self):
                return self._GetRegisterEvent(event)

            def setter(self, value):
                def getChecker():
                    if isinstance(value, testers.Tester):
                        value.TestValue = testValue
                        return value
                    elif isinstance(value, basestring):
                        return testers.GoldFile(File(self._TestRun, value, runtime=False),
                                                test_value=testValue)
                    elif isinstance(value, (tuple, list)):
                        return testers.GoldFileList([File(self._TestRun, item, runtime=False)
                                                     for item in value], test_value=testValue)

                self._RegisterChecker(event, getChecker)

            properties[name] = property(getter, setter)

        STREAMS = (
                   #std streams
                   ('stdout', 'Streams.stdout', 'StdOutFile'),
                   ('stderr', 'Streams.stderr', 'StdErrFile'),
                   #filtered streams
                   ('All', 'Streams.All', 'AllFile'),
                   ('Message', 'Streams.Message', 'MessageFile'),
                   ('Warning', 'Streams.Warning', 'WarningFile'),
                   ('Error', 'Streams.Error', 'ErrorFile'),
                   ('Debug', 'Streams.Debug', 'DebugFile'),
                   ('Verbose', 'Streams.Verbose', 'VerboseFile'),
                  )

        for name, event, testValue in STREAMS:
            createStreamProperty(name, event, testValue)
    __defineProperties__(locals())
    del __defineProperties__

class File(BaseTestRunItem):
    '''
    Allows us to test for a file. We can test for size, existance and content
    '''
    def __init__(self, testrun, name, exists = None, size = None, content_tester = None,execute=False,runtime=True):
        super(File, self).__init__(testrun)
        self.__name = name
        self.__runtime=runtime
        if exists:
            self.Exists = exists
        if size:
            self.Size = size
        if content_tester:
            self.Content = content_tester
        if execute:
            self.Execute = execute

    def __str__(self):
        return self.Name

    def GetContent(self,eventinfo):
        return self.AbsPath,""

    @property
    def AbsPath(self):
        '''
        The absolute path of the file, runtime value
        '''
        if self.__runtime:
            return self.AbsRunTimePath
        return self.AbsTestPath

    @property
    def AbsRunTimePath(self):
        '''
        The absolute path of the file, based on Runtime sandbox location
        '''
        return os.path.normpath(os.path.join(self._TestRun._Test.RunDirectory, self.Name))

    @property
    def AbsTestPath(self):
        '''
        The absolute path of the file, based on directory relative form the test file location
        '''
        return os.path.normpath(os.path.join(self._TestRun._Test.TestDirectory, self.Name))

    @property
    def Name(self):
        return self.__name

    @Name.setter
    def Name(self, val):
        self.__name = val

    @property
    def Exists(self):
        return self._GetRegisterEvent("File.Exists")

    @Exists.setter
    def Exists(self, val):
        def getChecker():
            if isinstance(val, testers.Tester):
                val.TestValue = self
                return val
            elif val == True:
                return testers.FileExists(True, self)
            elif val == False:
                return testers.FileExists(False, self)
        self._RegisterChecker('File.Exists', getChecker)

    def GetSize(self):
        statinfo = os.stat(self.AbsPath)
        return statinfo.st_size


    @property
    def Size(self):
        return self._GetRegisterEvent("File.Size")

    @Size.setter
    def Size(self, val):
        def getChecker():
            if isinstance(val, testers.Tester):
                val.TestValue = self
                return val
            else:
                return testers.Equal(int(val), test_value=self.GetSize)
        self._RegisterChecker('File.Size', getChecker)

    @property
    def Content(self):
        return self._GetRegisterEvent("File.Content")

    @Content.setter
    def Content(self, val):
        def getChecker():
            if isinstance(val, testers.Tester):
                val.TestValue = self
                return val
            elif isinstance(val, basestring):
                return testers.GoldFile(File(self._TestRun, val, runtime=False),
                                        test_value=self)
            elif isinstance(val, (tuple, list)):
                return testers.GoldFileList([File(self._TestRun, item, runtime=False)
                                             for item in val], test_value=self)

        self._RegisterChecker('File.Content', getChecker)

    @property
    def Executes(self):
        return self._GetRegisterEvent("File.Execute")

    @Executes.setter
    def Executes(self, val):
        def getChecker():
            if isinstance(val, testers.Tester):
                val.TestValue = self
                return val
            elif val == True:
                return testers.RunFile(True, self)
            elif val == False:
                return testers.RunFile(False, self)
            else:
                return testers.RunFile(val, self)
        self._RegisterChecker('File.Execute', getChecker)

class Directory(BaseTestRunItem):
    '''
    Allows us to test for a file. We can test for existance
    '''
    def __init__(self, testrun, name, exists = True, runtime=True):
        super(Directory, self).__init__(testrun)
        self.__name = name
        self.__runtime=runtime
        if exists:
            self.Exists = exists

    def __str__(self):
        return self.Name

    def GetContent(self, eventinfo):
        return self.AbsPath, ""

    @property
    def AbsPath(self):
        '''
        The absolute path of the file, runtime value
        '''
        if self.__runtime:
            return self.AbsRunTimePath
        return self.AbsTestPath

    @property
    def AbsRunTimePath(self):
        '''
        The absolute path of the file, based on Runtime sandbox location
        '''
        return os.path.normpath(os.path.join(self._TestRun._Test.RunDirectory, self.Name))

    @property
    def AbsTestPath(self):
        '''
        The absolute path of the file, based on directory relative form the test file location
        '''
        return os.path.normpath(os.path.join(self._TestRun._Test.TestDirectory, self.Name))

    @property
    def Name(self):
        return self.__name

    @Name.setter
    def Name(self, val):
        self.__name = val

    @property
    def Exists(self):
        return self._GetRegisterEvent("Directory.Exists")

    @Exists.setter
    def Exists(self, val):
        def getChecker():
            if isinstance(val, testers.Tester):
                val.TestValue = self
                return val
            elif val == True:
                return testers.DirectoryExists(True, self)
            elif val == False:
                return testers.DirectoryExists(False, self)
        self._RegisterChecker('Directory.Exists', getChecker)

class Disk(BaseTestRunItem):
    '''
    allows use to define what kind of disk based test we want to do
    '''
    def __init__(self,testrun):
        super(Disk, self).__init__(testrun)
        self.__files={}
        self.__dirs={}

    def File(self, name, exists=None, size=None, content=None, execute=None, id=None,
             runtime=True):
        tmp = File(self._TestRun, name, exists, size, content, execute, runtime)
        if self.__files.has_key(name):
            host.WriteWarning("Overriding file object {0}".format(name))
        self.__files[name] = tmp
        if id:
            self.__dict__[id] = tmp
        return tmp

    def Directory(self, name, exists=None, id=None, runtime=True):
        tmp = Directory(self._TestRun, name, exists, runtime)
        if self.__dirs.has_key(name):
            host.WriteWarning("Overriding directory object {0}".format(name))
        self.__dirs[name] = tmp
        if id:
            self.__dict__[id] = tmp
        return tmp

class TestRun(RegisterCheckerMixin, DelayedEventMapper):
    '''
    A test run allows us to test a certain command and see if certian actions happened as excepted
    Special cases of Test run may test it a test is up-to-date, or out-of -date
    '''
    class StreamNameReader(testers.Tester):
        def __init__(self, testRun):
            testers.Tester.__init__(self, None, False)
            self.testRun = testRun
            self.Result = testers.ResultType.Passed
            self.Reason = ''

        def test(self, eventinfo, **kw):
            self.testRun.StreamPaths = dict((name, getattr(eventinfo, name))
                                            for name in dir(eventinfo) if name.endswith('File'))

        @property
        def UseInReport(self):
            # exclude this checker from being used (and displayed) in the report since it
            # is not really a checker
            return False

    __slots__ = ["__displaystr", "__name", "__test", "__cmd", "__result", "__run_time",
                 "__disk", "__streams", "errorMessage", "StartingRun", "RunStarted", "Running",
                 "RunFinished", "StreamPaths"
               ]
    def __init__(self, test, name, displaystr=None):
        super(TestRun, self).__init__()
        #required setup
        self.__displaystr = displaystr # what we display for this string
        self.__name = name # the test name
        self.__test = test # test object

        # what to run
        self.__cmd = "" # this is the command we want to run

        # information about the run
        self.__result = None # the return code
        self.__run_time = None # the time in seconds of the run

        # objects with more stuff we can test.
        self.__disk = Disk(self)
        self.__streams = Streams(self)
        self.StreamPaths = {}

        #events that happen during run
        # these get mapped to test objects
        self.StartingRun = events.Event()
        self.RunStarted = events.Event()
        self.Running = events.Event()
        self.RunFinished = events.Event().Connect(self.StreamNameReader(self))

        # error message (if error happened)
        self.errorMessage = ''

    @property
    def _Test(self):
        return self.__test

    def get_testers(self):
        testers=[]
        testers+=list(self.StartingRun.Testers)
        testers+=list(self.RunStarted.Testers)
        testers+=list(self.Running.Testers)
        testers+=list(self.RunFinished.Testers)
        return testers

    @property
    def _Result(self):
        if self.__result is None:
            for i in self.get_testers():
                if self.__result < i.Result:
                    self.__result = i.Result
        #if we are have no result and have nothing to test
        # we say we passed
        if self.__result is None and len(self.get_testers()) == 0:
            self.__result = testers.ResultType.Passed
        return self.__result

    @_Result.setter
    def _Result(self,val):
        self.__result=val

    @property
    def Name(self):
        return self.__name

    @property
    def DisplayString(self):
        if self._displaystr:
            return self._displaystr
        return self.name

    @DisplayString.setter
    def DisplayString(self):
        if self.__displaystr:
            return self.__displaystr
        return self.Name

    @property
    def Command(self):
        return self.__cmd

    @Command.setter
    def Command(self,value):
        value=value.replace('/',os.sep)
        self.__cmd=value

    @property
    def RawCommand(self):
        return self.__cmd

    @RawCommand.setter
    def RawCommand(self,value):
        self.__cmd=value
    # stuff to test
    @property
    def ReturnCode(self):
        return self._GetRegisterEvent("TestRun.ReturnCode")

    @ReturnCode.setter
    def ReturnCode(self, val):
        def getChecker():
            if isinstance(val, testers.Tester):
                val.TestValue = 'ReturnCode'
                return val
            else:
                return testers.Equal(int(val), test_value='ReturnCode')
        self._RegisterChecker('TestRun.ReturnCode', getChecker, event=self.RunFinished)

    @property
    def Time(self):
        return self._GetRegisterEvent("TestRun.Time")

    @Time.setter
    def Time(self, val):
        def getChecker():
            if isinstance(val, testers.Tester):
                val.TestValue = 'TotalTime'
                return val
            else:
                return testers.Equal(int(val), test_value='TotalTime')
        self._RegisterChecker('TestRun.Time', getChecker, event=self.RunFinished)

    @property
    def TimeOut(self):
        return self._GetRegisterEvent("TestRun.TimeOut")

    @TimeOut.setter
    def TimeOut(self, val):
        def getChecker():
            if isinstance(val, testers.Tester):
                val.TestValue = 'TotalTime'
                return val
            else:
                return testers.LessThan(int(val), test_value='TotalTime', kill=True)
        self._RegisterChecker('TestRun.TimeOut', getChecker, event=self.Running)

    @property
    def Disk(self):
       return self.__disk

    @property
    def Streams(self):
       return self.__streams


