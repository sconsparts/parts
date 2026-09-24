Test.Summary = '''
CC_LAUNCHER and CXX_LAUNCHER wrap the compiles of a CMake() build, including a
launcher given with an argument and one whose path has a space. launch.sh logs each command it runs, so the
log shows which compiles went through it.
'''

# launch.sh is a POSIX shell script
Test.SkipIf(Condition.IsPlatform('windows'))
Test.SkipUnless(
    Condition.HasProgram('cmake', 'cmake is required to run this build'),
)

Setup.Copy.FromDirectory('launcher_cmake')

t = Test.AddBuildRun('all')
t.ReturnCode = 0
log = t.Disk.File('launch.log', exists=True)
log.Content = Testers.ContainsExpression(r'\[cmake\] .*cmake_main\.c', 'the CMake C compile went through CC_LAUNCHER, argument and all')
log.Content += Testers.ContainsExpression(r'\[spaced\] .*cmake_cxx\.cpp', 'the CMake C++ compile went through CXX_LAUNCHER, whose path has a space')
