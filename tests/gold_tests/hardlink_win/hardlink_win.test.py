import re

Test.Summary = '''
This is a test that checks that hardlinks on Windows don't cause failures upon rebuilds of
changed source. The test itself models being a compiler that blocks the source used for
compilation while Parts are trying to hardlink the same source to SDK which already has this
file hardlinked.
'''
#disable test for the moment as I want to relook at this "issue"
'''
def no_autoremove_sdk_files(data):
    match = re.search("dup: removing existing target .*sdks.*hello.c", data)
    if match:
        return 'SDK-installed file not marked as precious'

Test.SkipUnless(Condition.IsPlatform('windows'))

Setup.Copy.FromDirectory('source')

t = Test.AddBuildRun('all -j2')
t.ReturnCode = 0

t1 = Test.AddBuildRun('all -j2 dup_run=True --debug=duplicate')
t1.ReturnCode = 0

f = t1.Disk.File('logs/all.log')
f.Content = Testers.FileContentCallback(callback=no_autoremove_sdk_files,
                                        description = "Checking logs/all.log")

t2 = Test.AddBuildRun('all -j2 second_run=True --debug=duplicate --debug=stacktrace --verbose=ccopy')
t2.ReturnCode = 0
'''