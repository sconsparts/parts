import tester

class Equal(tester.Tester):
    def __init__(self,value,test_value=None,kill_on_failure=False):
        super(Equal,self).__init__(test_value=test_value,kill_on_failure=kill_on_failure)
        self.Description="Checking that {0} == {1}".format(tester.get_name(test_value),value)
        self._value=value
    
    def test(self,eventinfo, **kw):
        #Get value to test against
        val=self._GetContent(eventinfo)
        # do test
        if val != self._value:
            self.Result=tester.ResultType.Failed
            reason="Returned Value {0} != {1}".format(val,self._value)
            if self.KillOnFailure:
                self.Reason=reason+"\n Kill on failure is set".format(val,self._value)
                raise KillOnFailureError
            self.Reason=reason
        else:
            self.Result=tester.ResultType.Passed
            self.Reason="Returned Value: {0} == {1}".format(val,self._value)

