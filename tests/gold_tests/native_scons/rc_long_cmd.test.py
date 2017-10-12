import sys

Test.Summary = '''
This tests that resource compiler executes successfully when its command line exceeds 2 kb
'''
Test.SkipUnless(
    Condition.IsPlatform('windows')
)
Setup.Copy.FromDirectory('rc_long_cmd')

t = Test.AddBuildRun('all')
t.ReturnCode = 0
