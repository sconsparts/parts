Test.Summary = '''
This tests some value to types to InstallXXX() work as expected.
File should exist in the install and sdk areas
'''

Setup.Copy.FromDirectory('install1')

t = Test.AddBuildRun('all')
t.ReturnCode = 0
t.Disk.File("_install/lib/lib.so", exists=True)
t.Disk.File("_install/lib/lib1.so", exists=True)
t.Disk.File("_install/bin/foo.exe", exists=True)
t.Disk.File("_install/bin/foo1.exe", exists=True)

t.Disk.File("_install/include/dup.h", exists=True)
t.Disk.File("_install/include/sub1/dup.h", exists=True)
t.Disk.File("_install/include/top.h", exists=True)

t.Disk.File("_sdk/include/dup.h", exists=True)
t.Disk.File("_sdk/include/sub1/dup.h", exists=True)
t.Disk.File("_sdk/include/top.h", exists=True)

