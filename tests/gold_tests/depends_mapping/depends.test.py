Test.Summary = '''
This tests that the mapping of random data work as expected
'''
Setup.Copy.FromDirectory('depend1')

t = Test.AddBuildRun('all', '--verbose=gtest')
