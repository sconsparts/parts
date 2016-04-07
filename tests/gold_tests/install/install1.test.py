Test.Summary='''
This tests some value to types to InstallTarget()
'''

Setup.Copy.FromDirectory('install1')

t = Test.AddBuildRun('all')
t.ReturnCode = 0
t.Disk.File("_install/lib/lib.so",exists=True)
t.Disk.File("_install/lib/lib1.so",exists=True)
t.Disk.File("_install/bin/foo.exe",exists=True)
t.Disk.File("_install/bin/foo1.exe",exists=True)