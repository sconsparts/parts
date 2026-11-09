Test.Summary = '''
This test checks that two rpath-rewritable files with the same name, installed
under different sub_dirs, stage their runpath rewrites to different places.
Staged to one path, SCons stops with "Multiple ways to build the same target".
'''

Test.SkipUnless(
    Condition.HasProgram(
        program='rpmbuild',
        msg='Need to have rpmbuild tool on system to build the package',
    )
)

Setup.Copy.FromDirectory('rpm_rpath_subdir')

t = Test.AddBuildRun('.')
t.ReturnCode = 0
