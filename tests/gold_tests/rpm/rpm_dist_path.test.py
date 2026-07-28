import sys

Test.Summary = '''
This test checks that RPMPackage copies the built rpm into RPM_PACKAGE_DIST_PATH
when that variable is set, without a per-part env.CCopy(...) call.
'''

Test.SkipUnless(
    Condition.HasProgram(
        program='rpmbuild',
        msg='Need to have rpmbuild tool on system to build the package',
    )
)

Setup.Copy.FromDirectory('rpm_dist_path')

# RPM_PACKAGE_DIST_PATH is set in packaging.parts; building should place the
# rpm into that dist directory with no per-part CCopy.
t = Test.AddBuildRun('.')
t.ReturnCode = 0

# the built rpm (foo-1.0-1.x86.rpm) must land in the configured dist directory
t.Disk.File('_dist/foo-1.0-1.x86.rpm', exists=True)
