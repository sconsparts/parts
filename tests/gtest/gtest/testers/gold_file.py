import difflib
import json

import tester
import gtest.host as host

class GoldFile(tester.Tester):
    def __init__(self,goldfile,test_value=None,kill_on_failure=False):
        super(GoldFile,self).__init__(test_value=test_value,kill_on_failure=kill_on_failure)
        self.Description="Checking that {0} matches {1}".format(test_value,goldfile)
        self._goldfile=goldfile

    def test(self,eventinfo,**kw):
        #if not self._test_attibute(eventinfo,self.test_value):
         #   return
        #val=getattr(eventinfo,self.test_value)

        # get the attribute file context
        tmp=self._GetContent(eventinfo)
        if tmp is None:
            pass
        try:
            val_content=file(tmp).read()
        except (OSError, IOError), e:
            self.Result=tester.ResultType.Failed
            self.Reason=str(e)
            return

        # get the gold file context
        tmp=self._GetContent(eventinfo,self._goldfile)
        if tmp is None:
            pass
        try:
            gf_content=file(tmp).read()
        except:
            host.WriteError("Can't open file {0}".format(tmp))
        
        

        # make seqerncer differ
        seq=difflib.SequenceMatcher(None,val_content,gf_content)
        #do we have a match
        if seq.ratio() == 1.0:
            #The says ratio everything matched
            self.Result=tester.ResultType.Passed
            self.Reason="Values match"
            return
        # if we are here we don't have a match at the moment. At this point we process difference to see if they 
        # match and special code we have and do replacements of values and diff again to see if we have a match
        #get diffs
        results=seq.get_opcodes()
        newtext=''
        for tag, i1, i2, j1, j2 in results:
            # technically we can see that we might have a real diff
            # but we continue as this allow certain values to be replaced helping to make the 
            # finial diff string more readable
            if tag =="replace" :
                data=gf_content[j1:j2]
                tmp=self._do_action_replace(data,val_content[i1:i2])
                if tmp:
                    newtext+=tmp
                    continue

            if tag =="insert" :
                data=gf_content[j1:j2]
                tmp=self._do_action_add(data,val_content[i1:i2])
                if tmp is not None:
                    newtext+=tmp
                    continue
            
            newtext+=gf_content[j1:j2]

        #reset the sequence test 
        seq.set_seq2(newtext)
        if seq.ratio() == 1.0:
            #The says ratio everything matched
            self.Result=tester.ResultType.Passed
            self.Reason="Values match"
            return
        # this makes a nice string value.. 
        diff=difflib.Differ()
        self.Result=tester.ResultType.Failed
        tmp_result="\n".join(diff.compare(val_content.splitlines(),
                                              newtext.splitlines()
                                              )
                                 )
        
        self.Reason="File differences\nData File : {0}\nGold File : {1}\n{2}".format(
                            self._GetContent(eventinfo),
                            self._GetContent(eventinfo,self._goldfile),
                            tmp_result
                            )
        if self.KillOnFailure:
            raise KillOnFailureError

        # todo Change this logic to 
        # replace gold file text token with special values
        # special value is key, while orginial text is the "action"
        # on first diff we see if replace text matches key, if so we do action
        # note unique key need to be a safe, ideally control character that would not be typed 
        # or added to a text file normally
    def _do_action_replace(self,data,text):
        try:
            if data == "{}":
                return text
            # more options when we need them
            #elif data == "range":
               # pass
        except KeyError:
            # key are not found, so we assume we should default actions
            pass
        return None

    def _do_action_add(self,data,text):
        try:        
            if data == "{}":
                return ''
        except KeyError:
            pass
        return None

class GoldFileList(tester.Tester):
    def __init__(self, goldfilesList, test_value=None, kill_on_failure=False):
        super(GoldFileList, self).__init__(test_value=test_value,
                                          kill_on_failure=kill_on_failure)
        self.Description = "Checking that {0} matches one of {1}".format(test_value,
                ', '.join([str(gold) for gold in goldfilesList]))
        golds = []
        for goldfile in goldfilesList:
            golds.append(GoldFile(goldfile, test_value=test_value,
                                  kill_on_failure=kill_on_failure))
        self._golds = golds
        
    def test(self, eventinfo, **kw):
        results = []
        for gold in self._golds:
            gold.test(eventinfo, **kw)
            results.append(gold.Reason)
            if gold.Result == tester.ResultType.Passed:
                self.Result = tester.ResultType.Passed
                self.Reason = 'Gold file %s matched' % gold._goldfile
                return

        # there were no matching gold files found
        self.Result = tester.ResultType.Failed
        self.Reason = 'No matching gold files found, differences:\n%s' % '\n\n'.join(results)

    @property
    def TestValue(self):
        return self.__test_value

    @TestValue.setter
    def TestValue(self, value):
        self.__test_value = value
        for gold in self._golds:
            gold.TestValue = value
        
