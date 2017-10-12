Test.Summary = '''
Default() function works correctly.
'''

Setup.Copy.FromDirectory('src')
test_run = Test.AddBuildRun('')
test_run.ReturnCode = 0

hello_txt = test_run.Disk.File('install/bin/hello.txt')
hello_txt.Exists = True
hello_txt.Content = Testers.FileContentCallback(
    description='Checking "install/bin/hello.txt" contents',
    callback=lambda data: (
        ("Hello world!\n" != data and
         '"Hello world!\n" != "{data}"'.format(data=data)) or None
    )
)
# vim: set et ts=4 sw=4 ai :
