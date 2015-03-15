test.Summary="Test a condition that should pass"

Test.SkipUnless(
Condition.HasProgram(
                      "python",
                      "This test should always run because this program should exist."
                      ),
# unlikely to see Java, or ce or os2. add Java as it is more likely of these cases
Condition.IsPlatform('posix','windows','java')
)

t=Test.AddTestRun("This Test should run")
t.Command='echo "This Test should have run"'
t.ReturnCode=0