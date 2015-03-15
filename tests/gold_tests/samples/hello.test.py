Test.Summary='''
Basic test for making sure sample works
'''

Setup.Copy.FromSample('hello')


Test.AddOutOfDateCheck()

t=Test.AddBuildRun()

Test.AddUpdateCheck()
Test.AddCleanRun()
Test.AddOutOfDateCheck()

