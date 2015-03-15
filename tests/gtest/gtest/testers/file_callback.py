import tester

class FileContentCallback(tester.Tester):
    '''
    Class that is used to check file contents via some arbitrary function.
    
    Interface is as follows:
    
    def callback(data):
        return errorMessage
    
    where data is file contents (read by this class) and errorMessage is a string describing
    what's wrong with the file; if file is okay return '' or None from the callback
    
    For more usage examples see gold_tests/run_utest-timeout/run_utest-timeout.test.py
    '''
    def __init__(self, callback, description, killOnFailure=False):
        tester.Tester.__init__(self, None, kill_on_failure=killOnFailure)
        self.__callback = callback
        self.Description = description

    def test(self, eventinfo, **kw):
        absPath = self.TestValue.AbsPath
        result = tester.ResultType.Passed
        try:
            with open(absPath, 'r') as inp:
                data = inp.read()
        except IOError, err:
            result = tester.ResultType.Failed
            self.Reason = 'Cannot read {0}: {1}'.format(absPath, err)
        else:
            errorMessage = self.__callback(data)
            if errorMessage:
                result = tester.ResultType.Failed
                self.Reason = 'Contents of {0} do not match desired callback: {1}'.\
                              format(absPath, errorMessage)

        self.Result = result
        if result != tester.ResultType.Passed:
            if self.KillOnFailure:
                raise tester.KillOnFailureError()
        else:
            self.Reason = 'Contents of {0} match desired callback'.format(absPath)
