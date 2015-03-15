import re
import sys

# Currently this test is broken on MacOS X 10.4; we don't intend to support this platform,
# we intend to support 10.6 or higher, but we don't have it in INNL testing yet. Thus I'm
# disabling this test for MacOS < 10.6

def skipIfOldMac():
    if sys.platform == 'darwin':
        import platform
        macVer = [int(x) for x in re.findall(r'(\d+)', platform.mac_ver()[0])]
        return macVer >= [10, 6]
    return True

if sys.platform == 'win32':
    exe = '.exe'
else:
    exe = ''
Test.SkipUnless(Condition.Condition(function=skipIfOldMac, reason='MacOSX < 10.6 not supported',
                                    pass_value=True))

Test.Summary='''
This is a test that checks that a unit test that runs faster than specified timeout runs normally
while a unit test that takes too long to run is terminated by timeout
'''
Setup.Copy.FromDirectory('source')

t1 = Test.AddBuildRun('all utest:: -j2 -k --debug=time LOG_ROOT_DIR=#logs_build')
t1.ReturnCode = 0

t2 = Test.AddBuildRun('run_utest:: -j2 -k --debug=time LOG_ROOT_DIR=#logs_run_ut')
t2.ReturnCode = 2
logfile = t2.Disk.File('logs_run_ut/all.log')

TEST_LINES = [r'hello world from print_msg(); test #1 passed',
              r'scons: *** [run_utest::alias::print::test2] Killed by timeout (5.0 sec)']

def checkLogFile(data):
    for line in TEST_LINES:
        if not re.search(r'.*?^\s*{0}\s*$'.format(re.escape(line)), data,
                         re.MULTILINE | re.DOTALL):
            return 'line "{0}" not found in the log:\n{1}'.format(line, data)
    times = re.findall('Command execution time:\s+(\d+\.\d+)\s+seconds', data)
    if len(times) != 2:
        return 'unexpected amount of commands executed: %d' % len(times)

regexpTester = Testers.FileContentCallback(callback=checkLogFile,
                                           description='Checking all.log')
logfile.Exists = True
logfile.Content = regexpTester

run_utest1 = t2.Disk.File('logs_run_ut/run_utest.print_msg-test1_1.0.0{exe}.log'.format(exe = exe))
run_utest2 = t2.Disk.File('logs_run_ut/run_utest.print_msg-test2_1.0.0{exe}.log'.format(exe = exe))

def run_utest1_check(data):
    match = re.search("Elapsed time (\d+\.\d+) seconds", data)
    if not match:
        return '"Elapsed time N.NN seconds" string not found in the log'
    value = float(match.group(1))
    if value > 4:
        return 'successful test took too long: %f' % value

def run_utest2_check(data):
    match = re.search("Elapsed time (\d+\.\d+) seconds", data)
    if not match:
        return '"Elapsed time N.NN seconds" string not found in the log'
    value = float(match.group(1))
    if value < 4.5:
        return 'timed-out test was too fast: %f' % value
    if value > 10:
        return 'timed-out test was too long: %f' % value

run_utest1.Exists = True
run_utest1.Content = Testers.FileContentCallback(callback = run_utest1_check, description = "Successfull test")
run_utest2.Exists = True
run_utest2.Content = Testers.FileContentCallback(callback = run_utest2_check, description = "Timed out test")
