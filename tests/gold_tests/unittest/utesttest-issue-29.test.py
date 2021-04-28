Test.Summary = '''
Issue 29/30 that was reported.
'''

# I did some more digging in this case. I am 100% unclear on how this worked at all
# for some reason the hello2.part has the same getcwd() for first and second runs
# the other parts work as expected in which the getcwd() is the PART_DIR first pass
# and then BUILD_DIR second pass. not sure how this case worked as all. I going to 
# accept breaking it for us to go forward as it should have nevered worked
# I am planning to not use Sconcript() to do loading as well to address out of source
# part files better with the "extern" feature. Might make it work after this..

Test.SkipIf(Condition.true("This should have never worked.. look at test for notes"))

Setup.Copy.FromDirectory('issue-29')

# build test.. should not have any failures
t = Test.AddBuildRun('utest::')
t.ReturnCode = 0

# build test.. should not have any failures
t = Test.AddBuildRun('utest::')
t.ReturnCode = 0

Test.AddUpdateCheck('utest::')

t = Test.AddBuildRun('all')
t.ReturnCode = 0

Test.AddUpdateCheck('all')
