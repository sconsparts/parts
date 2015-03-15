Test.Summary='''
Basic test for making sure WDK works
'''

Test.SkipUnless(
    Condition.IsPlatform('windows'),
     Condition.HasRegKey(
                    HKEY_LOCAL_MACHINE,
                    [r'SOFTWARE\Wow6432Node\Microsoft\KitSetup\configured-kits',
                     r'SOFTWARE\Microsoft\KitSetup\configured-kits',
                     ],
                    "WDK not installed on the system"
                   )
    )
Setup.Copy.FromSample('wdk')

for config in ('debug', 'release'):
    # There is no 64-bit version for Windows XP
    Test.AddBuildRun('build:: config={0} DDK_MIN_WIN=wxp TARGET_ARCH=x86'.format(config))
    for version in ('wnet', 'wlh', 'win7'):
        for arch in ('x86', 'x86_64'):
            Test.AddBuildRun(
                    'build:: config={0} DDK_MIN_WIN={1} TARGET_ARCH={2}'.format(
                        config, version, arch))

# vim: set et ts=4 sw=4 ai ft=python :

