import sys

Test.Summary == '''
This test checks that the RPM builder adds files to RPM package from SConstruct.
To check the error when TARGET_ARCH = 'FakeArch'
'''

Test.SkipUnless(
    Condition.HasProgram(
        program='rpmbuild',
        msg='Need to have rpmbuild tool on system to build the package',
    )
)

Setup.Copy.FromDirectory('rpm_test2')

Test.AddBuildRun('.').ReturnCode = 2
