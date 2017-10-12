Test.Summary = '''
Test that the REQ.default(internal=True) works as expected
'''
Setup.Copy.FromDirectory('depend6')

t = Test.AddBuildRun('all', '--verbose=gtest')
t.Streams.Verbose = 'gold/depend6.gold'
