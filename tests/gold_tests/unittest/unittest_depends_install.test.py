Test.Summary = '''
The run of a unit test group must wait for the installs of the Parts that
unit_test.DependsOn() names. The test links against the _sdk copy of libA but
loads it from $INSTALL_LIB (RUNPATH $ORIGIN/../lib), so a run that starts
before A is installed exits with 127.
'''

# on darwin the dylib install name is a relative _build path, so the test
# cannot load libA.dylib even when A is installed first
Test.SkipUnless(Condition.IsPlatform('linux'))

Setup.Copy.FromDirectory('test_depends_install')

# unittest_depends_install_tree checks the alias graph; this run checks that
# A's install copies are in it and land before the test runs. Group 'other' does
# not compile, so the run also checks that one group does not build the others.
t = Test.AddBuildRun('run_utest::alias::B::test')
t.Streams.stdout = Testers.ContainsExpression(
    r'^cd _unit_tests/.* && \S+/bin/B-test_1\.0\.0', 'the test of group test must run')
