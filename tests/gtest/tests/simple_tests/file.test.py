#The finding of this test shows we find .test.py

Test.Summary="Test the existance, size and content of a file"

t=Test.AddTestRun("stdout")

t.Disk.File("log.txt",exists=True,id="logfile")
t.Disk.logfile.Content="gold/hello.gold"
if Condition.IsPlatform('win32'):
    t.Command='echo Hello >log.txt'
    t.Disk.logfile.Size=8
else:
    t.Command='echo "Hello ">log.txt'
    t.Disk.logfile.Size=7
t.Disk.File("fakelog.txt",id="fakelogfile")
t.Disk.fakelogfile.Exists=False