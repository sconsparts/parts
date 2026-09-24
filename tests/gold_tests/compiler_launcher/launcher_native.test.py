Test.Summary = '''
CC_LAUNCHER and CXX_LAUNCHER wrap native compiles, including a launcher given
with an argument and a compile whose command goes through a response file.
launch.sh logs each command it runs, so the log shows which compiles went
through it.
'''

# launch.sh is a POSIX shell script, and msvc does not use the launcher
Test.SkipIf(Condition.IsPlatform('windows'))

Setup.Copy.FromDirectory('launcher_native')

t = Test.AddBuildRun('all')
t.ReturnCode = 0
log = t.Disk.File('launch.log', exists=True)
log.Content = Testers.ContainsExpression(r'\[native\] .*native\.c', 'the C compile went through CC_LAUNCHER, argument and all')
log.Content += Testers.ContainsExpression(r'native_cxx\.cpp', 'the C++ compile went through CXX_LAUNCHER')
# MAXLINELENGTH=20 puts the whole compile in a response file; the launcher has
# to stay on the command line in front of the compiler and its @file
log.Content += Testers.ContainsExpression(r' @\S', 'the response-file compile went through CC_LAUNCHER')
