Test.Summary = '''
CC_LAUNCHER wraps the C compile of an AutoMake() build: it is folded into the
CC passed to configure. launch.sh logs each command it runs.
'''

# launch.sh is a POSIX shell script
Test.SkipIf(Condition.IsPlatform('windows'))
Test.SkipUnless(
    Condition.HasProgram('make', 'make is required to run this build'),
)

Setup.Copy.FromDirectory('launcher_automake')

t = Test.AddBuildRun('all')
t.ReturnCode = 0
log = t.Disk.File('launch.log', exists=True)
log.Content = Testers.ContainsExpression(r'\[automake\] .*automake_main\.c', 'the AutoMake compile went through CC_LAUNCHER, argument and all')
