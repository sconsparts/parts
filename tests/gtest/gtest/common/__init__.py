import time
import collections

def quirkyCompile(string, filename, mode='exec', flags=0, dont_inherit=0):
    '''
    Compiles a string into Python code object trying to workaround some quirks of Python 2.6
    '''
    return compile(string.replace('\r', '') + '\n', filename, mode, flags, dont_inherit)

class RunTimer(object):
    def __init__(self, ):
        self.events = collections.defaultdict(list)

    def startEvent(self, name):
        self.events[name].append((time.time(), None))
    
    def stopEvent(self, name):
        try:
            lastStampStart, lastStampFinish = self.events[name][-1]
        except IndexError:
            raise KeyError('No event "%s" was started' % name)
        if lastStampFinish:
            raise KeyError('Event "%s" was already marked as stopped' % name)
        self.events[name].pop()
        self.events[name].append((lastStampStart, time.time()))
    
    def getEvents(self):
        result = []
        for name, stamps in self.events.iteritems():
            for start, stop in stamps:
                if start and stop: # sanity check
                    result.append((name, stop - start))
        return sorted(result, key=lambda (name, duration): duration, reverse=True)
