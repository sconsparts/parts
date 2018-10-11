Test.Summary = '''
Checks that we are able to make the correct dependancy of A with B with a local mapping
'''

Setup.Copy.FromDirectory('match-basic.5')

# This should fail as the local mapping should not match
# and the global one should be ignored
tr = Test.AddBuildRun('.')
tr.ReturnCode = 2
