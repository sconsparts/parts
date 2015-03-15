Test.Summary='''
This tests that a basic empty Scons script will run with Parts
'''

Setup.Copy('sconstruct_simpesconstruct','sconstruct')

t=Test.AddTestRun("good")
t.Command="scons . --console-stream=none"
t.ReturnCode=0


