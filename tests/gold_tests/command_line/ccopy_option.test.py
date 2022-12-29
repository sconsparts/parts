Test.Summary = '''
This test the --ccopy_logic cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
Setup.Copy.FromTemplate('empty')

# note the --tc=null means we can set the target without issue of the tools complain
# that the can't setup correctly

t = Test.AddTestRun("good")
t.Command = "scons all --trace=ccopy_logic_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/ccopy_good0.gold'

t = Test.AddTestRun("good")
t.Command = "scons all --ccopy-logic=copy --trace=ccopy_logic_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/ccopy_good1.gold'

t = Test.AddTestRun("good")
t.Command = "scons all --copy-logic=copy --trace=ccopy_logic_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/ccopy_good1.gold'

t = Test.AddTestRun("good")
t.Command = "scons all --ccopy=copy --trace=ccopy_logic_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/ccopy_good1.gold'

# test differ cases of 'hard-soft-copy','soft-hard-copy','soft-copy','hard-copy','copy'
#t = Test.AddTestRun("good")
#t.Command = "scons all --ccopy=hard-soft-copy --trace=ccopy_logic_option --tc=null --console-stream=none"
#t.ReturnCode = 0
#t.Streams.Debug = 'gold/ccopy_good2.gold'

#t = Test.AddTestRun("good")
#t.Command = "scons all --ccopy=soft-hard-copy --trace=ccopy_logic_option --tc=null --console-stream=none"
#t.ReturnCode = 0
#t.Streams.Debug = 'gold/ccopy_good3.gold'

#t = Test.AddTestRun("good")
#t.Command = "scons all --ccopy=soft-copy --trace=ccopy_logic_option --tc=null --console-stream=none"
#t.ReturnCode = 0
#t.Streams.Debug = 'gold/ccopy_good4.gold'

t = Test.AddTestRun("good")
t.Command = "scons all --ccopy=hard-copy --trace=ccopy_logic_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/ccopy_good5.gold'

# error cases

t = Test.AddTestRun("bad")
t.Command = "scons all --ccopy-logic=hard --trace=ccopy_logic_option --tc=null --console-stream=none"
t.ReturnCode = 2
t.Streams.stderr = 'gold/ccopy_bad1.gold'

t = Test.AddTestRun("bad")
t.Command = "scons all --ccopy-logic=copy,foo --trace=ccopy_logic_option --tc=null --console-stream=none"
t.ReturnCode = 2
t.Streams.stderr = 'gold/ccopy_bad2.gold'
