Test.Summary='''
This tests use of default with nodes in it
'''

Setup.Copy.FromDirectory('default')

t=Test.AddTestRun("good")
t.Command="scons --console-stream=none"
t.ReturnCode=0
