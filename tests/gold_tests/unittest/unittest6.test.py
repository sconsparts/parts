Test.Summary='''
Test that Scons build the test given the relative node correctly
'''

Setup.Copy.FromDirectory('test6')

# build test.. should not have any failures
t=Test.AddBuildRun('utest:: -j3')

t.ReturnCode=0

