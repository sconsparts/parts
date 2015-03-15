Test.Summary='''
Basic test for making sure sample works
'''

Setup.Copy.FromSample('unit_test1')

t=Test.AddBuildRun("all")
t=Test.AddBuildRun("utest::")
Test.AddUpdateCheck('utest::')

