test.Summary="Test the setup of Setup Copy logic"

Test.SkipUnless(
Condition.HasProgram(
                      "svn",
                      "svn needs to be install and on the path"
                      )
)


Setup.Copy.FromDirectory("data")
Setup.Copy("data")

t=Test.AddTestRun("Test file existance")
t.Command='echo "do nothing"'
t.Disk.Directory("data",exists=True)
t.Disk.Directory("sub1").Exists=True


