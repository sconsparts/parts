Test.Summary = '''
Basic test for making sure symlinks works
'''

Test.SkipIf(
    Condition.IsPlatform('windows')
)
Setup.Copy.FromSample('symlinks_posix_only')

#t = Test.AddBuildRun('client')
#Test.AddBuildRun('symlinks2')
#Test.AddBuildRun()

## Test.AddUpdateCheck()
## Test.AddCleanRun()
## Test.AddOutOfDateCheck()
