

import os

import parts.logger as logger
import parts.ansi_stream as ansi_stream


class text(logger.Logger):

    def __init__(self, dir, file):
        if os.path.exists(dir) == False:
            os.makedirs(dir)
        self.m_file = open(os.path.join(dir, file), "w")
        super().__init__(dir, file)

    def logout(self, msg):
        msg=ansi_stream.strip_ansi_codes(msg)
        with self._lock:
            self.m_file.write(msg)

    def logerr(self, msg):
        msg=ansi_stream.strip_ansi_codes(msg)
        with self._lock:
            self.m_file.write(msg)

    def logwrn(self, msg):
        msg=ansi_stream.strip_ansi_codes(msg)
        with self._lock:
            self.m_file.write(msg)

    def logmsg(self, msg):
        msg=ansi_stream.strip_ansi_codes(msg)
        with self._lock:
            self.m_file.write(msg)

    def logtrace(self, msg):
        msg=ansi_stream.strip_ansi_codes(msg)
        with self._lock:
            self.m_file.write(msg)

    def logverbose(self, msg):
        msg=ansi_stream.strip_ansi_codes(msg)
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
