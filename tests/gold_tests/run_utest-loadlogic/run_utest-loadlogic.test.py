import re

# Currently this test is broken on MacOS X 10.4; we don't intend to support this platform,
# we intend to support 10.6 or higher, but we don't have it in INNL testing yet. Thus I'm
# disabling this test for MacOS < 10.6


def skipIfOldMac():
    import sys
    if sys.platform == 'darwin':
        import platform
        macVer = [int(x) for x in re.findall(r'(\d+)', platform.mac_ver()[0])]
        return macVer >= [10, 6]
    return True

Test.SkipUnless(Condition.Condition(function=skipIfOldMac, reason='MacOSX < 10.6 not supported',
                                    pass_value=True))
Test.SkipIf(Condition.true("Test turned off until load logic is re-enabled"))

Test.Summary = '''
Testing load-logic algorithms. When we run "scons run_utest::" command two times in a row
we expect Parts to load everything from files first time and from .cache second time.
'''
Setup.Copy.FromDirectory('source')

t1 = Test.AddBuildRun(
    'USE_CACHE_KEY=the.same run_utest:: -j2 --verbose=loading LOG_ROOT_DIR=#logs_1')
t1.ReturnCode = 0
t1Log = t1.Disk.File('logs_1/all.log')

t2 = Test.AddBuildRun(
    'USE_CACHE_KEY=the.same run_utest::name::main:: -j2 --verbose=loading LOG_ROOT_DIR=#logs_2')
t2.ReturnCode = 0
t2Log = t2.Disk.File('logs_2/all.log')

TEST_LINES = [
    r'Verbose: \[loading\] Loading everything as (there is no cache|the given targets are unknown)']


def checkPresence(data, test_lines):
    for line in test_lines:
        if not re.search(line, data, re.MULTILINE | re.DOTALL):
            return 'line "{0}" not found in the log:\n{1}'.format(line, data)
    return None


def checkAbsence(data, test_lines):
    for line in test_lines:
        if re.search(line, data, re.MULTILINE | re.DOTALL):
            return 'line "{0}" has been found in the log:\n{1}'.format(line, data)
    return None

t1Log.Exists = True
t1Log.Content = Testers.FileContentCallback(lambda data: checkPresence(
    data, TEST_LINES), description='Checking logs_1/all.log')

t2Log.Exists = True
t2Log.Content = Testers.FileContentCallback(lambda data: checkAbsence(data, TEST_LINES) or
                                            checkPresence(data, ['hello world from print_msg']), description='Checking logs_2/all.log')
