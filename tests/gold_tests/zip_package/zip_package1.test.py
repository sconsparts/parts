import sys

Test.Summary = '''
This test checks that ZipPackage adds files to zip if package names are specified
'''
Setup.Copy.FromDirectory('zip_package1')

t = Test.AddBuildRun('all', '.')

extension = '.exe' if sys.platform == 'win32' else ''
contains = ['bin/test1' + extension, 'bin/test2' + extension]

content_tester = Testers.ZipContent(includes=contains)
t.ReturnCode = 0
t.Disk.File("install.zip", exists=True, content=content_tester)
