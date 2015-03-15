Test.Summary='''
This test the basic ability to create a new entry and save it
'''
Setup.Copy('sconstruct_basic_save','sconstruct')

t=Test.AddBuildRun('.','--verbose=gtest')
t.Disk.File(".parts.cache/mytestkey/foo.cache",exists=True)

