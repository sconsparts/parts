Test.Summary='''
Test to see that a file with the form of #myprog/test/../.cc is processed correctly
'''
import sys

Setup.Copy.FromDirectory('parts-issue-1')

# run test.. should not have any failures
t = Test.AddBuildRun('utest::')
t.ReturnCode = 0
#verify file does not exist
if sys.platform == 'win32':
    t.Disk.File('myprog/test/unit/main-testhelper.obj',id='objectfile')
else:
    t.Disk.File('myprog/test/unit/main-testhelper.o',id='objectfile')
t.Disk.objectfile.exist=False



