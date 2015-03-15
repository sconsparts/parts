Test.Summary='''
This test case tests that depends on maps and part with no version to a range of *
Test cases give reported as a bug.. used as make sure regression does not happen
'''
Setup.Copy.FromDirectory('partsbug')

t=Test.AddBuildRun('all','--verbose=gtest')
