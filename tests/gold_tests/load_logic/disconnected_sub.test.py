Test.Summary='''
This test a the different load logic cases with a part that does not depend on its sub-parts
'''

Setup.Copy.FromTemplate('independent_subparts')

t=Test.AddTestRun("build-all")
t.Command="scons --console-stream=none all"
t.ReturnCode=0

Test.AddUpdateCheck()
Test.AddCleanRun()
Test.AddOutOfDateCheck()

t=Test.AddTestRun("build-target")
t.Command="scons --console-stream=none A --ll=all"
t.ReturnCode=0

Test.AddUpdateCheck('A')
Test.AddOutOfDateCheck('A.sub1')
Test.AddOutOfDateCheck('A.sub2')
Test.AddOutOfDateCheck('A.sub3')

t=Test.AddTestRun("build-target-target")
t.Command="scons --console-stream=none A:: --ll=target"
t.ReturnCode=0

Test.AddUpdateCheck()
Test.AddCleanRun()

t=Test.AddTestRun("build-target-min")
t.Command="scons --console-stream=none A:: --ll=min"
t.ReturnCode=0

Test.AddUpdateCheck()
Test.AddCleanRun()

t=Test.AddTestRun("build-target-unsafe")
t.Command="scons --console-stream=none A:: --ll=unsafe"
t.ReturnCode=0

Test.AddUpdateCheck()
Test.AddCleanRun()
