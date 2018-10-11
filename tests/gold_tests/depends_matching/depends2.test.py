Test.Summary = '''
Checks that we are able to make the correct dependancy of A with B
'''

Setup.Copy.FromDirectory('match-basic.2')

# This should pass
Test.AddBuildRun('.')
