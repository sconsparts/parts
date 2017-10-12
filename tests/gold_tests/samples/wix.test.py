Test.Summary = '''
This bunch of tests to test the WiX stuff.
'''
Test.SkipUnless(
    Condition.IsPlatform('windows'),
    Condition.HasRegKey(
        HKEY_LOCAL_MACHINE,
        [
            r'SOFTWARE\Microsoft\Windows Installer XML\3.5',
            r'SOFTWARE\Wow6432Node\Microsoft\Windows Installer XML\3.5',
            r'SOFTWARE\Microsoft\Windows Installer XML\3.6',
            r'SOFTWARE\Wow6432Node\Microsoft\Windows Installer XML\3.6',
            r'SOFTWARE\Microsoft\Windows Installer XML\3.7',
            r'SOFTWARE\Wow6432Node\Microsoft\Windows Installer XML\3.7',
            r'SOFTWARE\Microsoft\Windows Installer XML\3.8',
            r'SOFTWARE\Wow6432Node\Microsoft\Windows Installer XML\3.8',
            r'SOFTWARE\Microsoft\Windows Installer XML\3.9',
            r'SOFTWARE\Wow6432Node\Microsoft\Windows Installer XML\3.9',
            r'SOFTWARE\Microsoft\Windows Installer XML\3.10',
            r'SOFTWARE\Wow6432Node\Microsoft\Windows Installer XML\3.10',
            r'SOFTWARE\Microsoft\Windows Installer XML\3.11',
            r'SOFTWARE\Wow6432Node\Microsoft\Windows Installer XML\3.11',
        ],
        'WiX not installed on the system')
)

Setup.Copy.FromSample('wix')

Test.AddBuildRun()

# vim: set et ts=4 sw=4 ai :
