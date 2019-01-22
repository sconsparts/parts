Test.Summary = '''
Issue 29/30 that was reported
'''

Setup.Copy.FromDirectory('issue-29')

# build test.. should not have any failures
t = Test.AddBuildRun('utest::')
t.ReturnCode = 0

# build test.. should not have any failures
t = Test.AddBuildRun('utest::')
t.ReturnCode = 0

Test.AddUpdateCheck('utest::')

t = Test.AddBuildRun('all')
t.ReturnCode = 0

Test.AddUpdateCheck('all')
