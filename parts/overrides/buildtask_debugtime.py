'''
We monkey-patch SCons.Script.Main.BuildTask.execute() method to make sure commad execution
time statistics are gathered for all commands, even for those ending in some kind of
exception. We are also adding per-thread logging that could be enabled or disabled via
commandline option.
'''
from __future__ import absolute_import, division, print_function

import datetime
import errno
import os
import sys
import time

import SCons.Script
import SCons.Script.Main as Main
import SCons.Taskmaster

import _thread

EVENT_START, EVENT_STOP = 'start', 'stop'


def logTaskEvent(task, event, timestamp, duration=-1):
    try:
        if not logTaskEvent.storeLogsTo:
            return
    except AttributeError:
        # first call, let's find out if per-thread logging is enabled
        logTaskEvent.storeLogsTo = SCons.Script.GetOption('thread_logging_path')
        if not logTaskEvent.storeLogsTo:
            # per-thread logging is disabled, return immediately
            return
        logTaskEvent.storeLogsTo = os.path.abspath(logTaskEvent.storeLogsTo)

    try:
        os.makedirs(logTaskEvent.storeLogsTo)
    except OSError as err:
        # cannot mkdir this path... maybe it already exists?
        if err.errno != errno.EEXIST:
            # in the case when we cannot make logpath and the cause for that is *not*
            # that the path already exists we re-raise the exception
            raise
    if event == EVENT_START:
        try:
            executor = task.targets[0].get_executor()
            targets = executor.get_all_targets()
            sources = executor.get_all_sources()
            env = executor.get_build_env()
            taskLine = '\t'.join(repr(x) for x in (
                [str(t) for t in targets],
                [str(s) for s in sources],
                env.subst(str(executor), target=targets, source=sources))
            )
        except BaseException as substErr:
            taskLine = 'Cannot get task representation: %r' % substErr
    else:
        taskLine = 'duration=%.5f' % duration
    try:
        with open(os.sep.join([logTaskEvent.storeLogsTo, 'thread-%d.log' % _thread.get_ident()]),
                  'a+') as logFile:
            logFile.write('%s\t%s\t%s\n' % (datetime.datetime.fromtimestamp(timestamp), event,
                                            taskLine))
    except IOError:
        # cannot log there... raise for now
        raise


def patched_execute(self):
    try:
        enabled = logTaskEvent.storeLogsTo
    except AttributeError:
        # let's assume logging is enabled and let logTaskEvent deside that in itself
        enabled = True

    startTime = time.time()
    if enabled:
        logTaskEvent(self, EVENT_START, startTime)

    if Main.print_time:
        if Main.first_command_start is None:
            Main.first_command_start = startTime
    try:
        SCons.Taskmaster.OutOfDateTask.execute(self)
    finally:
        finishTime = time.time()
        if enabled:
            logTaskEvent(self, EVENT_STOP, finishTime, finishTime - startTime)
        if Main.print_time:
            Main.last_command_end = finishTime
            Main.cumulative_command_time += finishTime - startTime
            sys.stdout.write("Command execution time: %f seconds\n" % (finishTime - startTime))


Main.BuildTask.execute = patched_execute
