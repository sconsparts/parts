import sys

Test.Summary='''
This test checks that ZipPackage does not add files if no_pkg is specified
'''
Setup.Copy.FromDirectory('zip_package2')

t=Test.AddBuildRun('all', '.')

extension = '.exe' if sys.platform=='win32' else ''
contains = ['bin/test1' + extension]
notContains = ['bin/test2' + extension]

content_tester = Testers.ZipContent(includes=contains, excludes=notContains)
t.ReturnCode = 0
t.Disk.File("install.zip", exists=True, content=content_tester)
