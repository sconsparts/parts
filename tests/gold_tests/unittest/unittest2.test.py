Test.Summary = '''
Test that Scons build the test given the relative node correctly
'''

Setup.Copy.FromDirectory('test2')

# build test.. this should pass
t = Test.AddBuildRun('utest::')
t.ReturnCode = 0
