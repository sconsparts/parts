Test.Summary='''
Test that the UNIT_TEST_ENV works as expected
'''

Setup.Copy.FromDirectory('test_env')

# build test.. should not have any failures
t=Test.AddBuildRun('run_utest::')
t.ReturnCode=0

