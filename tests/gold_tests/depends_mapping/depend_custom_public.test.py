Test.Summary='''
This tests that the mapping of custom data work as expected in classic format, when mapped to public area
'''
Setup.Copy.FromDirectory('depend2')

t=Test.AddBuildRun('all','--verbose=gtest')
t.Streams.Verbose='gold/depend2.gold'
