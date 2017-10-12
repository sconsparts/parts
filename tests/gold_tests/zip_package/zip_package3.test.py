import sys

Test.Summary = '''
This test checks that ZipPackage does not add files if package name is None or empty string
'''
Setup.Copy.FromDirectory('zip_package3')

t = Test.AddBuildRun('all', '.')

extension = '.exe' if sys.platform == 'win32' else ''
contains = ['bin/test1' + extension]
notContains = ['bin/test2' + extension, 'bin/test3' + extension, 'bin/test4' + extension]

content_tester = Testers.ZipContent(includes=contains, excludes=notContains)
t.ReturnCode = 0
t.Disk.File("install.zip", exists=True, content=content_tester)
