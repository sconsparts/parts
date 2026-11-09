Test.Summary = '''
The run of an env.UnitTest() test must wait for the Parts that the part file's
env.DependsOn() names. env.UnitTest() makes the unit_test section depend on the
Part's own build section, which holds A's build alias.
'''

# on darwin the dylib install name is a relative _build path, so the test
# cannot load libA.dylib even when A is installed first
Test.SkipUnless(Condition.IsPlatform('linux'))

# a separate test from unittest_depends_install, so that no earlier run has
# installed A in the sandbox
Setup.Copy.FromDirectory('test_depends_install')

# the Part-level target that CI uses. Before the fix it also built A, through
# utest::alias::C, but after the test ran: at -j1 the run of the group comes
# first. At -jN the install usually won the race, so only -j1 checks the order.
t = Test.AddBuildRun('run_utest::C', '-j1')
t.Streams.stdout = Testers.ContainsExpression(
    r'^cd _unit_tests/.* && \S+/bin/C-test_1\.0\.0', 'the env.UnitTest() test must run')
