Test.Summary='''
Test that Scons build the test given the relative node correctly
'''

Setup.Copy.FromDirectory('test5')

# build test.. should not have any failures
t=Test.AddBuildRun('utest::')
t.ReturnCode=0

