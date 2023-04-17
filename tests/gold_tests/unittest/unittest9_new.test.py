Test.Summary = '''
Test that Scons build the test given the relative node correctly
'''

Setup.Copy.FromDirectory('test9_new')

# build test.. should not have any failures
t = Test.AddBuildRun('run_utest:: -j3')

t.ReturnCode = 0
