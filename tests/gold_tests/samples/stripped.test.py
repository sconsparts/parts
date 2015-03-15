Test.Summary='''
Testing separate debug info files creation on Darwin and Linux OSs
'''

Test.SkipIf(
    Condition.IsPlatform('windows')
    )

Setup.Copy.FromSample('stripped')

t=Test.AddBuildRun('build::')


