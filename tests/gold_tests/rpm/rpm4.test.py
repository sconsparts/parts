import sys

Test.Summary == '''
This test checks that the RPM builder adds files to RPM package from SConstruct.
without extension .rpm in packaging parts
'''

Test.SkipUnless(
    Condition.HasProgram(
        program='rpmbuild',
        msg='Need to have rpmbuild tool on system to build the package',
    )
)

Setup.Copy.FromDirectory('rpm_test4')

Test.AddBuildRun('.')
