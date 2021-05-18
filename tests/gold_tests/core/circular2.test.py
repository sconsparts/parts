Test.Summary = '''
Test circular dependency check.
'''
Setup.Copy.FromDirectory('circular-depends2')

t = Test.AddBuildRun("all",)
t.Processes.Default.ReturnCode = 2
