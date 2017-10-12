Test.Summary = '''
Test that run_utest:: targets output is put into separate log file.
'''
import os
import platform
import sys
import re


def getSystemName():
    PLATFORM_MAP = {'windows': 'win32',
                    'linux':   'posix',
                    'mac':     'darwin'}
    systemName = platform.system().lower()
    return PLATFORM_MAP.get(systemName, systemName)

Setup.Copy.FromDirectory('test7')

# run test.. should not have any failures
t = Test.AddBuildRun('run_utest:: -j3 TARGET_ARCH=x86')
t.ReturnCode = 0


def checkFile(data, file_name, regexp):
    if not re.search(regexp, data, re.MULTILINE):
        return "Regexp:\n{0}\nhas not been found in:\n{1}".format(regexp, data)

f = t.Disk.File('logs/all.log')
f.Content = Testers.FileContentCallback(callback=lambda data: checkFile(data, 'logs/all.log', 'done building targets'),
                                        description="Checking logs/all.log")

for one in ('', '1'):
    fname = 'logs/run_utest.root.utest-test{one}_1.0.0{suffix}.log'.\
        format(suffix='.exe' if platform.system().lower() == 'windows' else '', one=one)
    f = t.Disk.File(fname)
    f.Exists = True
    f.Content = Testers.FileContentCallback(callback=lambda data: checkFile(data, fname,
                                                                            r"return code = 1\nElapsed time \d+\.\d+ seconds".format(sep=os.sep, os=re.escape(getSystemName()), one=one)), description="Checking {fname}".format(**locals()))
