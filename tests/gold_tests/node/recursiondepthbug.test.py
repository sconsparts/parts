Test.Summary = '''
This tests some init behavior in the node that was found to cause stack overflow.
'''

Setup.Copy.FromDirectory('recursiondepthbug')

t = Test.AddTestRun("setup")
t.Command = "cd utest && scons --console-stream=none"
t.ReturnCode = 0

# the second pass should build
t = Test.AddTestRun()
t.Command = "cd utest && scons --console-stream=none"
t.ReturnCode = 0
