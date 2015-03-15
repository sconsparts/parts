import sys
Test.Summary='''
Test that the REQ.EXISTS works as expected
'''
Setup.Copy.FromDirectory('depend5')

t=Test.AddBuildRun('part2')

if sys.platform=='win32':
    t.Disk.File("install/bin/a1.exe",exists=True)
    t.Disk.File("install/bin/a2.exe",exists=True)
else:
    t.Disk.File("install/bin/a1",exists=True)
    t.Disk.File("install/bin/a2",exists=True)

Test.AddUpdateCheck('part2')
t=Test.AddCleanRun('part2')
if sys.platform=='win32':
    t.Disk.File("install/bin/a1.exe",exists=False)
    t.Disk.File("install/bin/a2.exe",exists=False)
else:
    t.Disk.File("install/bin/a1",exists=False)
    t.Disk.File("install/bin/a2",exists=False)
