import api
import console  # for stream types
import thread
import os

from SCons.Debug import logInstanceCreation


class Logger(object):

    def __init__(self, dir="", file=""):
        if __debug__:
            logInstanceCreation(self)
        self._lock = thread.allocate_lock()  # used to sync output

    def logout(self, msg):
        pass

    def logerr(self, msg):
        pass

    def logwrn(self, msg):
        pass

    def logmsg(self, msg):
        pass

    def logtrace(self, msg):
        pass

    def logverbose(self, msg):
        pass

    def ShutDown(self):
        self.shutdown()

    def shutdown(self):
        pass


class QueueLogger(Logger):

    def __init__(self, dir="", file=""):
        super(QueueLogger, self).__init__(dir, file)
        self.queue = []

    def logout(self, msg):
        self.queue.append((console.Console.out_stream, msg))

    def logerr(self, msg):
        self.queue.append((console.Console.error_stream, msg))

    def logwrn(self, msg):
        self.queue.append((console.Console.warning_stream, msg))

    def logmsg(self, msg):
        self.queue.append((console.Console.message_stream, msg))

    def logtrace(self, msg):
        self.queue.append((console.Console.trace_stream, msg))

    def logverbose(self, msg):
        self.queue.append((console.Console.verbose_stream, msg))


class nil_logger(Logger):
    pass


api.register.add_variable('LOGGER', 'NIL_LOGGER', '')

api.register.add_variable('TEXT_LOGGER', 'text', '')
api.register.add_variable('LOG_ROOT_DIR', '#logs', '')
api.register.add_variable('LOG_DIR', '${LOG_ROOT_DIR}', '')
api.register.add_variable('LOG_FILE_NAME', 'all.log', '')
