Test.Summary = '''
Test that Scons build the test given the relative node correctly
'''

Setup.Copy.FromDirectory('test7_new')

# build test.. should not have any failures
t = Test.AddBuildRun('utest:: -j3')

t.ReturnCode = 0
