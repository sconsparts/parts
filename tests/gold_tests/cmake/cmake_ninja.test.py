Test.Summary = '''
A CMake() build with the Ninja generator configures once. The second build of
an unchanged tree must not run the configure step again.
'''

# CMake() builds its configure and build steps as POSIX shell commands
# ("cd ... ;", "DESTDIR=... cmake"), which cmd.exe cannot run
Test.SkipIf(Condition.IsPlatform('windows'))
Test.SkipUnless(
    Condition.HasProgram('cmake', 'cmake is required to run this build'),
    Condition.HasProgram('ninja', 'ninja is required to run this build'),
)

Setup.Copy.FromDirectory('cmake_ninja')

t = Test.AddBuildRun('all')
t.ReturnCode = 0
t.Streams.stdout = Testers.ContainsExpression(r'-G "Ninja"', 'the first build configures with Ninja')

t = Test.AddBuildRun('all')
t.ReturnCode = 0
t.Streams.stdout = Testers.ExcludesExpression(r'-G "Ninja"', 'the second build does not configure again')
