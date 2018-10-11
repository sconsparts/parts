
Test.Summary = '''
This test checks that the dpkg adds files to deb from SConstruct
DefaultEnvironment is used.
Works fine without giving the path to dpkg-deb
'''

Test.SkipUnless(
    Condition.HasProgram(
        program='dpkg-deb',
        msg='Need to have dpkg-deb tool on system to build the package',
    ),
    Condition.HasProgram(
        program='debuild',        
        msg='Need to have debuild tool on system to build the package',
    )    
)


Setup.Copy.FromDirectory('test_dpkg1')

Test.AddBuildRun('.')
