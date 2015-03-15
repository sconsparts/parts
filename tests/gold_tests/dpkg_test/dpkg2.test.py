import sys

Test.Summary='''
This test checks that the dpkg-deb adds files to deb from Parts file 
DefaultEnvironment() is used in packaging.parts.
Works fine without giving the path to dpkg-deb
'''

Test.SkipUnless(
    Condition.HasProgram(
        program= 'dpkg-deb',
        #path = [r'/usr/bin/dpkg-deb'],
        msg='Need to have dpkg-deb tool on system to build the package',
    )
)
    

Setup.Copy.FromDirectory('test_dpkg2')

Test.AddBuildRun('all', '.')

