import imp
import os
import traceback
import sys
import unittest

def find_tests():
    addCleanupSupport()
    found, errors = [], []
    for root, dirs, files in os.walk('.'):
        #print 'Searching for tests in:', root
        if '.svn' in dirs:
            dirs.remove('.svn')
        for f in files:
            if f.endswith('.test.py'):
                print 'Loading tests from module', f,
                try:
                    found.append(my_load(root, f[:-3]))
                    print "- Succeeded!"
                    sys.stdout.flush()
                except:
                    print "- Failed! "
                    errors.append((f, traceback.format_exc()))
                    print >> sys.stderr, "Stack Dump %s" % ('-' * 40)
                    traceback.print_exc()
                    print >> sys.stderr, "Stack Dump - End %s" % ('-' * 40)
    return found, errors

def my_load(path, name):
    fp, pathname, description = imp.find_module(name, [path])
    try:
        return imp.load_module(name[:-5], fp, pathname, description)
    finally:
        # Since we may exit via an exception, close fp explicitly.
        if fp:
            fp.close()

def addCleanupSupport():
    if sys.version_info[:2] >= (2, 7):
        # Python 2.7+ already has this support, we don't need to do anything
        return
    if hasattr(unittest, 'ALREADY_PATCHED_FOR_CLEANUP'):
        # we've already patched this module, no need for re-patch
        return

    # injecting this function to store _resultForDoCleanups in self
    oldInit = unittest.TestCase.__init__
    def patchedInit(self, methodName='runTest'):
        oldInit(self, methodName)
        self._resultForDoCleanups = None
        self._cleanups = []
    unittest.TestCase.__init__ = patchedInit

    # injecting patched code that has some support for cleanup
    def patchedRun(self, result=None):
        if result is None:
            result = self.defaultTestResult()
        result.startTest(self)
        testMethod = getattr(self, self._testMethodName)
        try:
            ok = False
            try:
                self.setUp()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._exc_info())
            else:
                try:
                    testMethod()
                    ok = True
                except self.failureException:
                    result.addFailure(self, self._exc_info())
                except KeyboardInterrupt:
                    raise
                except:
                    result.addError(self, self._exc_info())

                try:
                    self.tearDown()
                except KeyboardInterrupt:
                    raise
                except:
                    result.addError(self, self._exc_info())
                    ok = False

            ok = self.doCleanups() and ok
            if ok:
                result.addSuccess(self)
        finally:
            result.stopTest(self)
    unittest.TestCase.run = patchedRun

    # backporting, i.e. copy-pasting, (by monkey-patching) the code from Python 2.7
    def addCleanup(self, function, *args, **kwargs):
        self._cleanups.append((function, args, kwargs))
    unittest.TestCase.addCleanup = addCleanup

    def doCleanups(self):
        result = self._resultForDoCleanups
        ok = True
        while self._cleanups:
            function, args, kwargs = self._cleanups.pop(-1)
            try:
                function(*args, **kwargs)
            except KeyboardInterrupt:
                raise
            except:
                ok = False
                result.addError(self, sys.exc_info())
        return ok
    unittest.TestCase.doCleanups = doCleanups

    _MAX_LENGTH = 80
    def safe_repr(obj, short=False):
        try:
            result = repr(obj)
        except:
            result = object.__repr__(obj)
        if not short or len(result) < _MAX_LENGTH:
            return result
        return result[:_MAX_LENGTH] + ' [truncated]...'
            
    def assertIsInstance(self, obj, cls, msg=None):
        if not isinstance(obj, cls):
            standardMsg = '%s is not an instance of %r' % (safe_repr(obj), cls)
            self.fail(self._formatMessage(msg, standardMsg))
    unittest.TestCase.assertIsInstance = assertIsInstance

    unittest.ALREADY_PATCHED_FOR_CLEANUP = True

if __name__ == '__main__':
    # for debugging
    addCleanupSupport()
