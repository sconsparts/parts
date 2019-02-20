from __future__ import absolute_import, division, print_function

import collections
import errno
import os
import subprocess
import sys
import time
import unittest

try:
    from SCons.Errors import UserError
except ImportError:
    UserError = Exception


class ProcessAction(object):
    SUSPEND = 'suspend'
    TERMINATE = 'terminate'
    RESUME = 'resume'


def _callWithCheck(message, *call_args, **call_kw):
    call_kw['stdout'] = subprocess.PIPE
    call_kw['stderr'] = subprocess.PIPE
    proc = subprocess.Popen(*call_args, **call_kw)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        raise UserError(message.format(proc.returncode, '%s\n\n%s' % (stdout.decode(), stderr.decode())))
    return stdout.decode()


if os.name == 'nt':
    import ctypes
    from ctypes.wintypes import DWORD, HANDLE, BOOL, FILETIME, LARGE_INTEGER
    LPFILETIME = ctypes.POINTER(FILETIME)
    LPLARGE_INTEGER = ctypes.POINTER(LARGE_INTEGER)

    # constants taken from MSDN
    TH32CS_SNAPPROCESS = 0x2    # snapshot all the processes on the system
    TH32CS_SNAPTHREAD = 0x4     # snapshot all the threads on the system
    THREAD_SUSPEND_RESUME = 0x2  # suspend or resume a thread
    PROCESS_TERMINATE = 0x1     # terminate a process
    PROCESS_QUERY_INFORMATION = 0x400  # required to get process times

    MAX_PATH = 260

    SmallProcessInfo = collections.namedtuple('SmallProcessInfo', 'name pid ppid')
    SmallThreadInfo = collections.namedtuple('SmallThreadInfo', 'tid pid')

    class ProcessEntry32(ctypes.Structure):
        _fields_ = [('dwSize', DWORD),
                    ('cntUsage', DWORD),
                    ('th32ProcessID', DWORD),
                    ('th32DefaultHeapID', ctypes.POINTER(ctypes.c_ulong)),
                    ('th32ModuleID', DWORD),
                    ('cntThreads', DWORD),
                    ('th32ParentProcessID', DWORD),
                    ('pcPriClassBase', ctypes.c_long),
                    ('dwFlags', DWORD),
                    ('szExeFile', ctypes.c_char * MAX_PATH)]

        def __init__(self):
            ctypes.Structure.__init__(self)
            self.dwSize = ctypes.sizeof(self)

        def getInfo(self):
            return SmallProcessInfo(self.szExeFile, self.th32ProcessID, self.th32ParentProcessID)

    class ThreadEntry32(ctypes.Structure):
        _fields_ = [('dwSize', DWORD),
                    ('cntUsage', DWORD),
                    ('th32ThreadID', DWORD),
                    ('th32OwnerProcessID', DWORD),
                    ('tpBasePri', ctypes.c_long),
                    ('tpDeltaPri', ctypes.c_long),
                    ('dwFlags', DWORD)]

        def __init__(self):
            ctypes.Structure.__init__(self)
            self.dwSize = ctypes.sizeof(self)

        def getInfo(self):
            return SmallThreadInfo(self.th32ThreadID, self.th32OwnerProcessID)

    WaitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
    WaitForSingleObject.restype = DWORD
    WaitForSingleObject.argtypes = (HANDLE, DWORD)

    CloseHandle = ctypes.windll.kernel32.CloseHandle
    CloseHandle.restype = BOOL
    CloseHandle.argtypes = (HANDLE, )

    CreateToolhelp32Snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot
    CreateToolhelp32Snapshot.restype = HANDLE
    CreateToolhelp32Snapshot.argtypes = (DWORD, DWORD)

    Process32First = ctypes.windll.kernel32.Process32First
    Process32First.argtypes = (HANDLE, ctypes.POINTER(ProcessEntry32))
    Process32First.restype = BOOL

    Process32Next = ctypes.windll.kernel32.Process32Next
    Process32Next.argtypes = (HANDLE, ctypes.POINTER(ProcessEntry32))
    Process32Next.restype = BOOL

    Thread32First = ctypes.windll.kernel32.Thread32First
    Thread32First.argtypes = (HANDLE, ctypes.POINTER(ThreadEntry32))
    Thread32First.restype = BOOL

    Thread32Next = ctypes.windll.kernel32.Thread32Next
    Thread32Next.argtypes = (HANDLE, ctypes.POINTER(ThreadEntry32))
    Thread32Next.restype = BOOL

    OpenThread = ctypes.windll.kernel32.OpenThread
    OpenThread.argtypes = (DWORD, BOOL, DWORD)
    OpenThread.restype = HANDLE

    SuspendThread = ctypes.windll.kernel32.SuspendThread
    SuspendThread.argtypes = (HANDLE, )
    SuspendThread.restype = DWORD

    OpenProcess = ctypes.windll.kernel32.OpenProcess
    OpenProcess.argtypes = (DWORD, BOOL, DWORD)
    OpenProcess.restype = HANDLE

    TerminateProcess = ctypes.windll.kernel32.TerminateProcess
    TerminateProcess.argtypes = (HANDLE, ctypes.c_uint)
    TerminateProcess.restype = BOOL

    DebugActiveProcess = ctypes.windll.kernel32.DebugActiveProcess
    DebugActiveProcess.argtypes = (DWORD,)
    DebugActiveProcess.restype = BOOL

    DebugActiveProcessStop = ctypes.windll.kernel32.DebugActiveProcessStop
    DebugActiveProcessStop.argtypes = (DWORD,)
    DebugActiveProcessStop.restype = BOOL

    GetProcessTimes = ctypes.windll.kernel32.GetProcessTimes
    GetProcessTimes.argtypes = (HANDLE, LPFILETIME, LPFILETIME, LPFILETIME, LPFILETIME)
    GetProcessTimes.restype = BOOL

    def int_to_handle(value):
        '''
        Casts Python integer to ctypes.wintypes.HANDLE
        '''
        return ctypes.cast(
            ctypes.pointer(ctypes.c_size_t(value)),
            ctypes.POINTER(ctypes.wintypes.HANDLE)).contents

    def __waitForProcess(process, timeout):
        # WaitForSingleObject expects timeout in milliseconds, so we convert it
        WaitForSingleObject(int_to_handle(process._handle), int(timeout * 1000))

    def _traverseWinStructures(snapFlags, entryClass, traverseFirst, traverseNext):
        snapHandle = CreateToolhelp32Snapshot(snapFlags, 0)
        if snapHandle == HANDLE(-1):
            raise ctypes.WinError()
        try:
            entry = entryClass()
            res = traverseFirst(snapHandle, ctypes.pointer(entry))
            if not res:
                raise ctypes.WinError()
            while res:
                yield entry.getInfo()
                res = traverseNext(snapHandle, ctypes.pointer(entry))
        finally:
            CloseHandle(snapHandle)

    def __getProcessCreationTime(pid):
        '''
        returns process creation time
        '''
        handle = OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
        if handle == 0:
            return None
        try:
            created, exited, kernel, user = FILETIME(), FILETIME(), FILETIME(), FILETIME()
            if not GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited),
                                   ctypes.byref(kernel), ctypes.byref(user)):
                return None
            return ctypes.cast(ctypes.pointer(created), LPLARGE_INTEGER).contents.value
        finally:
            CloseHandle(handle)

    def _listAllProcesses():
        for name, pid, ppid in _traverseWinStructures(TH32CS_SNAPPROCESS, ProcessEntry32,
                                                      Process32First, Process32Next):
            # Windows does not set process parent id to 0 when the parent dies
            # we need to detect such sitation. We use the fact that parent
            # is always older then a child.
            processCreated = __getProcessCreationTime(pid)
            if processCreated is None:
                # if we cannot read from the process we don't care about it
                # because it is not in our sub-tree or it may be dead.
                continue
            parentCreated = __getProcessCreationTime(ppid)
            if (parentCreated is None) or (parentCreated >= processCreated):
                # Parent is not accessible -> pid is orphan
                # Parent is younger than pid -> pid is orphan
                ppid = None
            yield pid, ppid

    def _listAllThreads():
        for entry in _traverseWinStructures(TH32CS_SNAPTHREAD, ThreadEntry32,
                                            Thread32First, Thread32Next):
            yield entry

    def suspendThread(tid):
        threadHandle = OpenThread(THREAD_SUSPEND_RESUME, False, tid)
        if threadHandle == 0:
            raise ctypes.WinError()
        try:
            if SuspendThread(threadHandle) == DWORD(-1):
                raise ctypes.WinError()
        finally:
            CloseHandle(threadHandle)

    def suspendProcess(pid):
        if not DebugActiveProcess(pid):
            # if DebugActiveProcess failed try to suspend threads one by one
            for tid, ownerPid in _listAllThreads():
                if ownerPid == pid:
                    suspendThread(tid)

    def terminateProcess(pid):
        procHandle = OpenProcess(PROCESS_TERMINATE, False, pid)
        if procHandle == 0:
            raise ctypes.WinError()
        try:
            if TerminateProcess(procHandle, 128) == 0:
                raise ctypes.WinError()
        finally:
            CloseHandle(procHandle)

    PROCESS_ACTIONS = {ProcessAction.SUSPEND: suspendProcess,
                       ProcessAction.TERMINATE: terminateProcess,
                       ProcessAction.RESUME: DebugActiveProcessStop}

    def _performAction(pid, action):
        try:
            PROCESS_ACTIONS[action](pid)
        except BaseException as e:
            raise UserError('Cannot {2} PID {0}: {1}'.format(pid, e, action))

elif os.name == 'posix':
    import signal
    import time
    import re

    def __waitForProcess(process, timeout):
        startTime = time.time()
        endTime = startTime + timeout
        while (time.time() < endTime) and (process.poll() is None):
            time.sleep(0.1)

    if sys.platform == 'cygwin':
        _PS_CALL_CMD = ['ps', '-eW']
    else:
        _PS_CALL_CMD = ['ps', '-A', '-o', 'pid,ppid,stat']

    def _listAllProcesses():
        out = _callWithCheck('Cannot get the list of running processes: ps rc = {0}, '
                             'output = {1}', _PS_CALL_CMD)
        lines = out.splitlines()
        if not re.match(r'\s*PID\s+PPID', lines[0]):
            raise UserError('Bad ps output header: {0}'.format(lines[0]))
        for line in lines[1:]:
            try:
                pid, ppid, stat = re.match(r'^\s*(\d+)\s+(\d+)\s+(\S+)', line).groups()
                if not stat.startswith('Z'):
                    yield int(pid), int(ppid)
            except ValueError:
                raise UserError('Bad line in ps output: {0}'.format(line.strip()))

    ACTION_SIGNALS = {ProcessAction.SUSPEND: [signal.SIGSTOP],
                      ProcessAction.TERMINATE: [signal.SIGTERM, signal.SIGKILL],
                      ProcessAction.RESUME: [signal.SIGCONT]}

    def _performAction(pid, action):
        for sigNumber in ACTION_SIGNALS[action]:
            try:
                os.kill(pid, sigNumber)
            except OSError as e:
                if e.errno != errno.ESRCH:
                    raise UserError('Cannot {2} PID {0}: {1}'.format(pid, e, action))
            except BaseException as e:
                raise UserError('Cannot {2} PID {0}: {1}'.format(pid, e, action))

else:
    raise ImportError('Unsupported OS: %s' % os.name)


def _getRunningProcesses():
    ''' returns a dict mapping parent pid to a list of children pids '''
    result = collections.defaultdict(list)
    for pid, ppid in _listAllProcesses():
        result[ppid].append(pid)
    return result


def killProcessTree(proc):
    killQueue = list()

    def fillQueue(pid):
        _performAction(pid, ProcessAction.SUSPEND)
        killQueue.append(pid)
        for item in _getRunningProcesses()[pid]:
            fillQueue(item)
        return killQueue

    for pid in fillQueue(proc.pid):
        _performAction(pid, ProcessAction.TERMINATE)
        _performAction(pid, ProcessAction.RESUME)


def waitForProcess(process, timeout=None):
    if timeout is None:
        try:
            process.wait()
        except OSError as e:
            if e.errno != errno.ECHILD:
                raise
    else:
        __waitForProcess(process, timeout)


class TestKillProcessTree(unittest.TestCase):
    if os.name == 'nt':
        pause = 'pause'
        pwd = 'cd'
        null = 'nul'
        sep = '&'
    else:
        pause = 'read'
        pwd = 'pwd'
        null = '/dev/null'
        sep = ';'

    def test_nozombie(self):
        zombie = subprocess.Popen('{pause} > {null} 2>&1 {sep} {pwd} > {null} 2>&1'.format(
            pause=self.pause, pwd=self.pwd, null=self.null, sep=self.sep),
            stdin=subprocess.PIPE,
            shell=True)
        pid = zombie.pid
        time.sleep(0.1)  # Give zombie time to start
        proclist1 = _getRunningProcesses()[os.getpid()]
        zombie.stdin.write('\n'.encode())
        time.sleep(0.5)  # Give zombie time to die
        proclist2 = _getRunningProcesses()[os.getpid()]
        zombie.wait()  # Shoot it!
        self.assertTrue(pid in proclist1)
        self.assertFalse(pid in proclist2)


if __name__ == '__main__':
    unittest.main()
