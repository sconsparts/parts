import sys

Test.Summary='''
This tests some AbsFileNode for items out of tree.
'''

Setup.Copy.FromDirectory('absnode')

# run test.. should not have any failures
t = Test.AddBuildRun('utest:: all')
t.ReturnCode = 0
#verify file does not exist
if sys.platform == 'win32':
    t.Disk.File('myprog/test/unit/main-testhelper.obj',id='objectfile')
    t.Disk.File('myprog/test2/unit/main-testhelper2.obj',id='objectfile2')
else:
    t.Disk.File('myprog/test/unit/main-testhelper.o',id='objectfile')
    t.Disk.File('myprog/test2/unit/main-testhelper2.o',id='objectfile2')
t.Disk.objectfile.exist=False
t.Disk.objectfile2.exist=False

