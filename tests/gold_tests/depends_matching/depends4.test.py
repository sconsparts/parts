Test.Summary = '''
Checks that we are able to make the correct dependancy of A with B with a local mapping
'''

Setup.Copy.FromDirectory('match-basic.4')

# This should pass as the local mapping should allow a match
# not an ambigous match
Test.AddBuildRun('.')
