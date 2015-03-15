Test.Summary='''
This test that a single REQ.item is mapped correctly. bug was that it is not turned into a REQ set correctly
'''
Setup.Copy.FromDirectory('depend4')

t=Test.AddBuildRun('all','--verbose=gtest')
t.Streams.Verbose='gold/depend4.gold'
