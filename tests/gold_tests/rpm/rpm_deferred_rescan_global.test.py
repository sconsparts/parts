Test.Summary = '''
This test checks that a global package group node, whose file list was not
known when it was first scanned, is scanned again once the global
package.groups.jsn turns out to be up to date.

As in rpm_deferred_rescan, the second build gives the rpm a new release and
rebuilds a header in the group with the same content. Here the group is global,
and the second build targets the rpm file. Before the fix the group node kept
the partial dependency list of its first, deferred scan (package.groups.jsn
only), so it did not wait for its files, and every later build rebuilt it
because the header was "a new dependency".
'''

Test.SkipUnless(
    Condition.HasProgram(
        program='rpmbuild',
        msg='Need to have rpmbuild tool on system to build the package',
    )
)

Setup.Copy.FromDirectory('rpm_deferred_rescan_global')

t = Test.AddBuildRun('all', extra='-release-1')
t.Disk.File('release.txt').WriteOn('1\n')
t.Disk.File('stamp.txt').WriteOn('a\n')
t.Disk.File('dist/lib1-devel-1.0-1.x86_64.rpm', exists=True)

t = Test.AddBuildRun('dist/lib1-devel-1.0-2.x86_64.rpm', extra='-release-2')
t.Disk.File('release.txt').WriteOn('2\n')
t.Disk.File('stamp.txt').WriteOn('b\n')
t.Disk.File('dist/lib1-devel-1.0-2.x86_64.rpm', exists=True)

Test.AddUpdateCheckParts()
