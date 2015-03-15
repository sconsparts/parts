Test.Summary='''
This tests that a basic empty Scons script will run with Parts
'''
# fix this test to verify that the error is what we expect

Setup.Copy('sconstruct_simpesconstruct_error','sconstruct')

t=Test.AddTestRun("good")
t.Command="scons . --console-stream=none"
t.ReturnCode=2


