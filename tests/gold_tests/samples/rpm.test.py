import sys

Test.Summary == '''
This test checks that the RPM builder adds files to RPM package from SConstruct.
'''

Test.SkipUnless(
    Condition.HasProgram(
        program='rpmbuild',
        msg='Need to have rpmbuild tool on system to build the package',
    )
)

Setup.Copy.FromSample('rpm')

Test.AddBuildRun('.')
