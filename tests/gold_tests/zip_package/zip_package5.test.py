import sys

Test.Summary='''
This test checks that ZipPackage does not add files if no package name specified
'''
Setup.Copy.FromDirectory('zip_package5')

t=Test.AddBuildRun('all', '.')
t.ReturnCode = 0
extension = '.exe' if sys.platform=='win32' else ''
notContains = ['bin/test1' + extension, 'bin/test2' + extension]

content_tester = Testers.ZipContent(excludes=notContains)
t.ReturnCode = 0
t.Disk.File("install.zip", exists=True, content=content_tester)
