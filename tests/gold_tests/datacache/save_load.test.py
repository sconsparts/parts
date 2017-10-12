Test.Summary = '''
This test the basic ability to create a new entry and save it and then load it
'''
Setup.Copy('sconstruct_save_load', 'sconstruct')

t = Test.AddBuildRun('.', '--verbose=gtest')
t.Disk.File(".parts.cache/mytestkey/foo.cache", exists=True)
t.Streams.Verbose = 'gold/save_load.gold'

# test that if we only load that this works
t = Test.AddBuildRun('.', '--verbose=gtest load_only=True')
t.Streams.Verbose = 'gold/save_load.gold'
