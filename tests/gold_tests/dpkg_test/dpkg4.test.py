import sys

Test.Summary = '''
This test checks that the dpkg adds files to deb from SConstruct 
and checks if the deb file exists, if the package name 
and destination folder name ('dist' in this case) is provided 
Works fine without giving the path to dpkg-deb.
'''

Test.SkipUnless(
    Condition.HasProgram(
        program='dpkg-deb',
        #path = [r'/usr/bin/dpkg-deb'],
        msg='Need to have dpkg-deb tool on system to build the package',
    )
)


Setup.Copy.FromDirectory('test_dpkg4')

t = Test.AddBuildRun('all', '.')

extension = '.exe' if sys.platform == 'win32' else ''
contains = ['bin/test1' + extension, 'bin/test2' + extension]

t.ReturnCode = 0
t.Disk.File("dist/cpil_1.0_all.deb", exists=True)
