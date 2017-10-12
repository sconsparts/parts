Test.Summary = '''
Basic test for making sure symlinks works
'''

Test.SkipIf(
    Condition.IsPlatform('windows')
)
Setup.Copy.FromSample('symlinks')

t = Test.AddBuildRun()

# Test.AddUpdateCheck()
# Test.AddCleanRun()
# Test.AddOutOfDateCheck()
