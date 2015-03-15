test.Summary="Test a condition that should fail, so this should always skip"

#this case will fail
Test.SkipUnless(Condition.HasProgram("DOESNOTEXISTPROGRAM","This test should always be skipped because this program should not exist."))


t=Test.AddTestRun("This Test should not run")
t.Command='echo "This Test should not have run"'
t.ReturnCode=5