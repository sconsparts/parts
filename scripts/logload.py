'''
Helper script that allows working with per-thread Parts logs
'''

import glob
import sys
import datetime

class LogLine(object): #pylint: disable=too-few-public-methods
    '''
    Class that knows how to parse the line in per-thread logs produced by Parts
    '''

    UNPACK = ['targets', 'sources', 'command']
    __slots__ = ['timestamp', 'event', 'duration'] + UNPACK

    def __init__(self, line, previousLogs=None):
        timestamp, rest = line.split('\t', 1)
        if '.' in timestamp:
            self.timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
        else:
            self.timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')

        if rest.startswith('start'):
            # those variables are used indirectly - they're accessed by locals()[key], but
            # pylint cannot detect that, so I'm squelching its report here
            event, targets, sources, command = rest.split('\t') #pylint: disable=unused-variable
            self.duration = None
        elif rest.startswith('stop'):
            event = 'stop'
            try:
                previousLogLine = previousLogs[-1]
            except: #pylint: disable=bare-except
                targets, sources, command = None, None, None
            else:
                targets, sources, command = previousLogLine.targets, previousLogLine.sources, \
                                            previousLogLine.command
                previousLogLine.duration = (self.timestamp - previousLogLine.timestamp).\
                                            total_seconds()
        else:
            raise ValueError('unexpected line format: %r' % line)
        self.event = event
        unpackRequest = dict([(unpackName, locals()[unpackName]) for unpackName in self.UNPACK])
        result = self.unpack(unpackRequest)
        for unpackName in self.UNPACK:
            setattr(self, unpackName, result[unpackName])

    @staticmethod
    def unpack(valuesDict):
        '''
        Unpacks the valuesDict (a dict mapping name to encoded value) to a real dict with
        decoded values within
        '''
        result = {}
        newLocals = {'result': result}
        for name, value in valuesDict.iteritems():
            try:
                exec 'result["%s"] = %s' % (name, value) in newLocals #pylint: disable=exec-used
            except: #pylint: disable=bare-except
                result[name] = value
        return result

    def __str__(self):
        return '%s (%.3f)\t%s\t%s' % (self.timestamp, self.duration, self.event,
                # LogLine actually has .command member, but it's set via setattr() call so
                # pylint cannot detect that
                self.command[:40] + ('...' if len(self.command) > 40 else '')) #pylint: disable=no-member

    def __repr__(self):
        return repr(self.__str__())

class LogLineNoParse(LogLine): #pylint: disable=too-few-public-methods
    '''
    Faster version of LogLine that doesn't decode any values, suitable for e.g. automating
    some statistics counting
    '''
    @staticmethod
    def unpack(valuesDict):
        # don't decode anything, just return a copy of incoming dict back
        return dict(valuesDict)

def loadLogFile(path, logLineClass=LogLine):
    '''
    Loads one per-thread log pointed by path and returns a list of LogLines
    '''
    temp = []
    with open(path, 'r') as logFile:
        for line in logFile:
            try:
                logLine = logLineClass(line.strip(), temp)
            except BaseException as err:
                print "Error: {0}.\n  Line: {1}".format(err, line)
            else:
                temp.append(logLine)

    result = []
    for logLine in temp:
        if logLine.event != 'start':
            continue
        if logLine.duration is not None:
            logLine.event = 'done'
        else:
            logLine.duration = float('inf')
        result.append(logLine)
    return result

def main(args): #pylint: disable=missing-docstring
    if not args:
        print >> sys.stderr, \
            'Usage: {0} log-file-or-files-to-load\nExample: {0} logs\\*'.format(sys.argv[0])
        return 1
    result = []
    for arg in args:
        for fileName in glob.glob(arg):
            result += loadLogFile(fileName)

    # now work with results interactively
    import pdb
    pdb.set_trace()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))