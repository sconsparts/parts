Test.Summary = '''
This test the --mode cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
Setup.Copy.FromTemplate('empty')

# note the --tc=null means we can set the target without issue of the tools complain
# that the can't setup correctly
t = Test.AddTestRun("good")
t.Command = "scons all --mode=foo --trace=mode_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/mode_good1.gold'

t = Test.AddTestRun("good")
t.Command = "scons all --trace=mode_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/mode_good2.gold'

t = Test.AddTestRun("good")
t.Command = "scons all --mode=foo,boo --trace=mode_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/mode_good3.gold'
