Test.Summary = '''
This tests that the env.AbsFileNode work correctly with subparts in out of source and repo case.
'''

Setup.Copy.FromDirectory('outofsource')

# test a simple part
t = Test.AddBuildRun('comp1')
t.ReturnCode = 0

#test a subpart case
t = Test.AddBuildRun('comp2')
t.ReturnCode = 0

# clean everything
t= Test.AddCleanRun("all")

#test a subpart case
t = Test.AddBuildRun('all')
t.ReturnCode = 0