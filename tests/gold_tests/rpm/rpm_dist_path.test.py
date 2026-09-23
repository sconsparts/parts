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

# RPM_PACKAGE_DIST_PATH is set in packaging.parts. The part's ::dist alias
# builds the copy there on its own.
t = Test.AddBuildRun('build::alias::packaging::dist')
t.ReturnCode = 0
t.Disk.File('_dist/foo-1.0-1.x86.rpm', exists=True)

# A full build also runs the part's own CCopy of the rpm into #dist, which has
# to see one rpm, not the rpm and the dist copy of it.
t = Test.AddBuildRun('.')
t.ReturnCode = 0
t.Disk.File('_dist/foo-1.0-1.x86.rpm', exists=True)
t.Disk.File('dist/foo-1.0-1.x86.rpm', exists=True)
