Test.Summary = '''
This test basic meson support
'''
Test.SkipUnless(
    Condition.HasProgram(
        program='meson',
        msg='meson must be present to test it'
    )
)

Setup.Copy.FromDirectory('source')

t = Test.AddBuildRun('all')
t.ReturnCode = 0
t.Streams.stdout = 'gold/extern0.gold'
