Test.Summary = '''
This tests that the mapping of custom data work as expected in classic format
'''
Setup.Copy.FromDirectory('depend1')

t = Test.AddBuildRun('all', '--verbose=gtest')
t.Streams.Verbose = 'gold/depend1.gold'
