Test.Summary = '''
This test checks that an rpm whose package group was not ready when the rpm was
first scanned is scanned again once the group node turns out to be up to date.

The second build gives the rpm a new release, so its target and _rpm directory
are new, and rebuilds a header in the group with the same content, so the
package group node is visited but not rebuilt. Before the fix the rpm kept the
empty dependency list of its first, deferred scan, and rpmbuild ran without a
spec file ("failed to stat .../SPECS/*").

The second build targets the packaging part, not "all": with "all" whether the
rpm is scanned before the header is rebuilt depends on the walk order, and the
test could pass without the fix.
'''

Test.SkipUnless(
    Condition.HasProgram(
        program='rpmbuild',
        msg='Need to have rpmbuild tool on system to build the package',
    )
)

Setup.Copy.FromDirectory('rpm_deferred_rescan')

t = Test.AddBuildRun('all', extra='-release-1')
t.Disk.File('release.txt').WriteOn('1\n')
t.Disk.File('stamp.txt').WriteOn('a\n')
t.Disk.File('dist/lib1-devel-1.0-1.x86_64.rpm', exists=True)

t = Test.AddBuildRun('packaging', extra='-release-2')
t.Disk.File('release.txt').WriteOn('2\n')
t.Disk.File('stamp.txt').WriteOn('b\n')
t.Disk.File('dist/lib1-devel-1.0-2.x86_64.rpm', exists=True)

Test.AddUpdateCheckParts()
