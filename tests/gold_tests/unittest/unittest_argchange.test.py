Test.Summary = '''
Test that Scons build the test when the arg value changes
'''

Setup.Copy.FromDirectory('test_args')

# build test.. should not have any failures
t = Test.AddBuildRun('utest::', 'MYARGS="foo bar"')
t.ReturnCode = 0

# Test should be up to date
t = Test.AddUpdateCheck('utest:: MYARGS="foo bar"')

# change the arguments passed, should be out of date
t = Test.AddOutOfDateCheck('utest::')
