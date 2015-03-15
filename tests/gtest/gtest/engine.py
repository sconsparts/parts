import os
import shutil
import test
import runtesttask
import setup
import host
import glb
import testers
from fnmatch import fnmatch
from common.pathutils import remove_read_only
from common import quirkyCompile, RunTimer
from common.threadpool import ThreadPool
from report import TestsReport
import time

class Engine(object):
    """description of class"""

    def __init__(self, host, jobs=1, test_dir='./', run_dir="./_sandbox", gtest_site=None,
                 filter_in='*', dump_report=False):
        self.__host = host
        self.__tests = {}
        self.__jobs = jobs
        self.__test_dir = test_dir
        self.__run_dir = os.path.abspath(run_dir)
        self.__gtest_site = gtest_site
        self.__filter_in = filter_in
        self.__dump_report = dump_report
        self.__timer = RunTimer()
        if jobs > 1:
            self.__pool = ThreadPool(jobs)
        if glb.Engine:
            raise RuntimeError("Only one engine can be created at a time")
        glb.Engine = self

    def Start(self):
        self.__timer.startEvent('total')
        if os.path.exists(self.__run_dir):
            self.__timer.startEvent('sandbox cleanup')
            host.WriteVerbose("engine", "The Sandbox directory exists, will try to remove")
            oldExceptionArgs = None
            while True:
                try:
                    shutil.rmtree(self.__run_dir, onerror=remove_read_only)
                except BaseException, e:
                    if e.args != oldExceptionArgs:
                        # maybe this is Windows issue where antivirus won't let us remove
                        # some random directory, so we're waiting & retrying
                        oldExceptionArgs = e.args
                        time.sleep(1)
                        continue
                    host.WriteError(("Unable to remove sandbox directory for clean test run" + \
                                     "\n Reason: {0}").format(e), show_stack=False)
                    raise
                else:
                    # no exceptions, the directory was wiped
                    break
            host.WriteVerbose("engine", "The Sandbox directory was removed")
            self.__timer.stopEvent('sandbox cleanup')
        self.__timer.startEvent('extensions load')
        host.WriteVerbose("engine", "Loading Extensions")
        self._load_extensions()
        self.__timer.stopEvent('extensions load')
        self.__timer.startEvent('scanning for tests')
        host.WriteVerbose("engine", "Scanning for tests")
        self._scan_for_tests()
        self.__timer.stopEvent('scanning for tests')
        host.WriteVerbose("engine", "Running tests")
        self._run_tests()
        self.__timer.startEvent('making report')
        host.WriteVerbose("engine", "Making report")
        result = self._make_report()
        self.__timer.stopEvent('making report')
        self.__timer.stopEvent('total')
        for eventName, eventDuration in self.__timer.getEvents():
            host.WriteVerbose('durations', '%s - %.2f sec.' % (eventName.ljust(40), eventDuration))
        return result

    def _load_extensions(self):
        # load files of our extension type in the directory

        locals={
                'AddTestRunSet':test.AddTestRunSet,
                'AddSetupTask':setup.AddSetupTask,
                'SetupTask':setup.SetupTask,
                }
        if self.__gtest_site is None:
            path=os.path.join(self.__test_dir,'gtest-site')
        else:
            path=os.path.abspath(self.__gtest_site)
        if os.path.exists(path):
            host.WriteVerbose("engine","Loading Extensions from {0}".format(path))
            for f in os.listdir(path):
                f=os.path.join(path,f)
                if os.path.isfile(f) and f.endswith("test.ext"):
                    self._load_file(f,locals,locals)
        else:
            host.WriteVerbose("engine","gtest-site path not found")



    def _scan_for_tests(self):

        ret=[]
        for root, dirs, files in os.walk(self.__test_dir):
            host.WriteVerbose("test_scan","Looking for tests in",root)

            for f in files:
                if f.endswith('.test.py') or f.endswith(".test"):
                    if f.endswith('.test.py'):
                        name=f[:-len('.test.py')]
                    else:
                        name=f[:-len('.test')]

                    if not fnmatch(name, self.__filter_in):
                        continue

                    if self.__tests.has_key(name):
                        host.WriteWarning("overiding test",name, "with test in", root)
                    host.WriteVerbose("test_scan","   Found test",name)
                    self.__tests[name]=test.Test(name,root,f,self.__run_dir,self.__test_dir)

    def _run_tests(self):
        if self.__jobs > 1:
            for t in self.__tests.itervalues():
                self.__pool.addTask(self.__run_test_task, t)
            self.__pool.waitCompletion()
        else:
            for t in self.__tests.itervalues():
                self.__run_test_task(t)

    def __run_test_task(self, task):
        self.__timer.startEvent('running test <%s>' % task.Name)
        runtesttask.RunTestTask(task)()
        self.__timer.stopEvent('running test <%s>' % task.Name)

    def _load_file(self, file, globals=None, locals=None):
        host.WriteVerbose("engine", "Loading file: {0}", file)
        with open(file, 'r') as f:
            exec(quirkyCompile(f.read(), file), globals or {}, locals or {})
        #print g


    def _make_report(self):
        report = TestsReport()
        for test in self.__tests.itervalues():
            report.addTestRun(test)
        host.WriteMessage("\nReport: --------------")
        for msg in report.exportForConsole():
            host.WriteMessage(msg)
        host.WriteMessage("")
        if sum([report.stats[resType] for resType in (testers.ResultType.Exception,
                                                      testers.ResultType.Failed,
                                                      testers.ResultType.Unknown,
                                                      testers.ResultType.Warning)]) > 0:
            host.WriteMessage('Test run had isses!')
            runResult = 1
        else:
            host.WriteMessage('All tests passed')
            runResult = 0
        for resType in (testers.ResultType.Unknown, testers.ResultType.Exception,
                        testers.ResultType.Failed,  testers.ResultType.Warning,
                        testers.ResultType.Skipped, testers.ResultType.Passed):
            amount = report.stats[resType]
            host.WriteMessage(' %s: %s' % (testers.ResultType.to_string(resType), amount))

        if self.__dump_report:
            host.WriteMessage('\n\n{JSON_REPORT}%s{/JSON_REPORT}' % report.exportForJson())
        return runResult

    @property
    def Host(self):
        return self.__host
