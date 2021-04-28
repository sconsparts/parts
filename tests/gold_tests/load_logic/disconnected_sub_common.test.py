Test.Summary = '''
This test a the different load logic cases with a part that does not depend on its sub-parts
Each sub-part of A depends on a common headers. This tests some mapping logic with platform_indpendent
and with not using platform_indpendent (default case). Use of sub-parts to to make example a little more
complex stressing the logic in better
'''

# note on the test .. currently we are redoing the internals.. so --load-logic may not stay around
# because of this items below maybe disabled.. will need to review and clean up test as needed


Setup.Copy.FromTemplate('independent_subparts_common_shared')

t = Test.AddTestRun("build-all")
t.Command = "scons --console-stream=none all"
t.ReturnCode = 0

Test.AddUpdateCheck()
Test.AddCleanRun()
Test.AddOutOfDateCheck()

t = Test.AddTestRun("build-target")
t.Command = "scons --console-stream=none A --ll=all"
t.ReturnCode = 0

Test.AddUpdateCheck('A')
Test.AddOutOfDateCheck('A.sub1')
Test.AddOutOfDateCheck('A.sub2')
Test.AddOutOfDateCheck('A.sub3')

t = Test.AddTestRun("build-target-target")
t.Command = "scons --console-stream=none A:: --ll=target"
t.ReturnCode = 0

Test.AddUpdateCheck("A::")

t = Test.AddTestRun("build-target-min")
t.Command = "scons --console-stream=none A:: --ll=min"
t.ReturnCode = 0

Test.AddUpdateCheck("A::")

t = Test.AddTestRun("build-target-unsafe")
t.Command = "scons --console-stream=none A:: --ll=unsafe"
t.ReturnCode = 0

# this should look up to date
Test.AddUpdateCheck("A::")

# target "all" some state files for the root common.part 
# that should not have been built yet
# -- This is disabled with the rework in the internals.. --
#Test.AddOutOfDateCheckParts() 

Test.AddBuildRun()

Test.AddUpdateCheck()
Test.AddCleanRun()
