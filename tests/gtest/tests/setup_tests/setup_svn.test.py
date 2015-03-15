test.Summary="Test the setup of SVN logic"

Test.SkipUnless(
                Condition.HasProgram(
                      "svn",
                      "svn needs to be install and on the path"
                      )
)                      

Setup.Svn.CreateRepository("mysvn")
Setup.Svn.ImportDirectory("mysvn","data","trunk/test")

t=Test.AddTestRun("svn checkout")
t.RawCommand='svn co "$MYSVN_SVN_PATH/trunk" myco'
t.ReturnCode=0
t.Disk.Directory("myco/test/sub1",exists=True)
t.Disk.File("myco/test/sub1/a.txt").Exists=True

