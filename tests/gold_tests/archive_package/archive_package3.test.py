import sys

Test.Summary == '''
This test checks that the archive builder adds files to archive package from SConstruct.
Test for various archive packages along with dpkg
'''

Test.SkipUnless(
    Condition.HasProgram(
        program='dpkg-deb',
        msg='Need to have dpkg-deb tool on system to build the package',
    )
)

Setup.Copy.FromDirectory('archive_package3')

Test.AddBuildRun('.')
