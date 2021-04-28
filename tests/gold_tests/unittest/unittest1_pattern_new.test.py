Test.Summary = '''
Test that Scons build the test given the relative node correctly
'''

Setup.Copy.FromDirectory('test1_pattern_new')

# build test.. this should pass
t = Test.AddBuildRun('utest::')
t.ReturnCode = 0
