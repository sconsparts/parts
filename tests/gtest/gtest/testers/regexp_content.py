import re

import tester
from file_callback import FileContentCallback

class RegexpContent(FileContentCallback):
    def __init__(self, regexp, description, killOnFailure=False):
        if isinstance(regexp, basestring):
            regexp = re.compile(regexp)
        self.__regexp = regexp
        FileContentCallback.__init__(self, self.__check, description, killOnFailure)
    
    def __check(self, data):
        if not self.__regexp.search(data):
            return 'Contents of {0} do not match desired regexp'.format(self.TestValue.AbsPath)
