import sys

Test.Summary = '''
This test checks that Extract works correctly
'''
Setup.Copy.FromDirectory('extract1')

t = Test.AddBuildRun('all')
t.ReturnCode = 0
if sys.platform == 'win32':
    t.Disk.File("install/bin/Test.exe", exists=True)
else:
    t.Disk.File("install/bin/test", exists=True)
