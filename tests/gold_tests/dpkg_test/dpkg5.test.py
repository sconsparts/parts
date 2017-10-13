import sys

Test.Summary = '''
This test checks that the dpkg-deb adds files to deb from Parts file
In this both zip and dpkg builders are used.
Works fine without giving the path to dpkg-deb.
'''

Test.SkipUnless(
    Condition.HasProgram(
        program='dpkg-deb',
        msg='Need to have dpkg-deb tool on system to build the package',
    )
)


Setup.Copy.FromDirectory('test_dpkg5')

Test.AddBuildRun('all', '.')
