Test.Summary = '''
Checks that we are able to make the correct dependancy of A with B
'''

Setup.Copy.FromDirectory('match-basic.3')

# This should fail at the moment .. 
# Needs to be fixed I think. The mapping logic fails to map less
# complex component requirement when more more complex mapping
# exists. The work around is to map in the correct component manually
# as in test case 4
tr = Test.AddBuildRun('.')
tr.ReturnCode = 2
