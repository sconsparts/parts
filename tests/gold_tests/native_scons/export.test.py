Test.Summary = '''
Test that the export logic does not break.
'''

Setup.Copy.FromDirectory('export')

t = Test.AddTestRun()
t.Processes.Default.Command = "scons --console-stream=none"
t.Processes.Default.ReturnCode = 2
t.Processes.Default.Streams.stdout="gold/export.gold"
