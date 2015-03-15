'''
Report object that knows how to print itself and can be exported to a file
'''
from testers.tester import ResultType
import collections
import json

class TestsReport(object):
    ITEM_PASS =    'passed'
    ITEM_SKIPPED = 'skipped'
    ITEM_NOTRUN =  'not run'
    ITEM_OTHER =   'other'

    def __init__(self):
        self.testRuns = {}
        self.stats = collections.defaultdict(int)

    def addTestRun(self, test):
        if test._Result == ResultType.Skipped:
            message = (self.ITEM_SKIPPED, str(test._Conditions._Reason))
        elif test._Result == ResultType.Passed:
            message = (self.ITEM_PASS, None)
        elif test.Setup._Failed:
            message = (self.ITEM_NOTRUN, str(test.Setup._Reason))
        else:
            runs = []
            for tr in test._TestRuns:
                if tr._Result == ResultType.Passed:
                    runMessage = (self.ITEM_PASS, None)
                elif tr._Result == ResultType.Skipped:
                    runMessage = (self.ITEM_SKIPPED, 'previous test run failed.')
                elif tr._Result == ResultType.Exception and tr.errorMessage:
                    runMessage = (self.ITEM_NOTRUN, tr.errorMessage)
                else:
                    checkers = []
                    for check in tr.get_testers():
                        if not check.UseInReport:
                            continue
                        if check.Result == ResultType.Passed:
                            reason = None
                        else:
                            reason = str(check.Reason)
                        checkers.append((check.Description, ResultType.to_string(check.Result),
                                         reason, False))
                    try:
                        with open(tr.StreamPaths['AllFile'], 'r') as streamBoth:
                            checkers.append(('stream.both.txt', 'contents below:',
                                             streamBoth.read(), True))
                    except KeyError:
                        # no such file stream, probably nothing was built
                        pass
                    runMessage = (self.ITEM_OTHER, checkers)
                runs.append((tr.Name, ResultType.to_string(tr._Result)) + runMessage)
            message = (self.ITEM_OTHER, runs)
        self.testRuns[(test.TestDirectory, test.TestFile)] = message
        self.stats[test._Result] += 1

    def _asStrList(self, testDir, testFile, addStreamBoth=False):
        status, message = self.testRuns[(testDir, testFile)]

        if status != self.ITEM_PASS:
            yield '\nTest run "{0}" in directory "{1}"'.format(testFile, testDir)
            if status == self.ITEM_SKIPPED:
                yield '  Skipped: %s' % message
            elif status == self.ITEM_NOTRUN:
                yield '  Setup failed: %s' % message
            else:
                for runName, statusStr, runStatus, runMessage in message:
                    yield '\n  %s: %s' % (runName, statusStr)
                    if runStatus != self.ITEM_OTHER:
                        if runMessage:
                            yield '    Reason: %s' % runMessage
                    else:
                        for description, result, reason, streamBoth in runMessage:
                            if streamBoth and not addStreamBoth:
                                continue
                            yield '    Check: %s - %s' % (description, result)
                            if reason:
                                yield '      Reason: %s' % reason

    def exportForConsole(self):
        for testDir, testFile in self.testRuns.iterkeys():
            for msg in self._asStrList(testDir, testFile):
                yield msg

    def exportForJson(self):
        result = []
        for (testDir, testFile), (status, msg) in self.testRuns.iteritems():
            messages = [msg for msg in self._asStrList(testDir, testFile, addStreamBoth=True)]
            result.append((testDir, testFile, status, '\n'.join(messages)))
        return json.dumps(result)

