Test.Summary = '''
A CMake() build with CMAKE_GENERATOR='Unix Makefiles': the name has a space in
it, so it has to reach cmake as one quoted -G argument. The second build of an
unchanged tree must not run the configure step again.
'''

Test.SkipUnless(
    Condition.HasProgram('cmake', 'cmake is required to run this build'),
    Condition.HasProgram('make', 'make is required to run this build'),
)

Setup.Copy.FromDirectory('cmake_unix_makefiles')

t = Test.AddBuildRun('all')
t.ReturnCode = 0
t.Streams.stdout = Testers.ContainsExpression(r'-G "Unix Makefiles"', 'the first build configures with Unix Makefiles')

t = Test.AddBuildRun('all')
t.ReturnCode = 0
t.Streams.stdout = Testers.ExcludesExpression(r'-G "Unix Makefiles"', 'the second build does not configure again')
