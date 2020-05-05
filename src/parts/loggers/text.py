
from __future__ import absolute_import, division, print_function

import os

import parts.logger as logger


class text(logger.Logger):

    def __init__(self, dir, file):
        if os.path.exists(dir) == False:
            os.makedirs(dir)
        self.m_file = open(os.path.join(dir, file), "w")
        super(text, self).__init__(dir, file)

    def logout(self, msg):
        with self._lock:
            self.m_file.write(msg)

    def logerr(self, msg):
        with self._lock:
            self.m_file.write(msg)

    def logwrn(self, msg):
        with self._lock:
            self.m_file.write(msg)

    def logmsg(self, msg):
        with self._lock:
            self.m_file.write(msg)

    def logtrace(self, msg):
        with self._lock:
            self.m_file.write(msg)

    def logverbose(self, msg):
        with self._lock:
            self.m_file.write(msg)

    def shutdown(self):
        if ('m_file' in self.__dict__) == False:
            return
        self.m_file.close()

    def __del__(self):
        try:
            self.m_file.close()
        except Exception:
            pass
