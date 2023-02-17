import sys

Test.Summary == '''
This test checks that the RPM spec generator makes has no requires
'''

Test.SkipUnless(
    Condition.HasProgram(
        program='rpmbuild',
        msg='Need to have rpmbuild tool on system to build the package',
    )
)

Setup.Copy.FromDirectory('rpm_test7')

t = Test.AddBuildRun('.')
t.Disk.File("_build/rpm/_rpm/a-1.2.3-1parts.x86_64/SPECS/a-1.2.3-1parts.x86_64.spec", exists=True).Content = Testers.ExcludesExpression("Requires:", "Should not contain Requires key")

