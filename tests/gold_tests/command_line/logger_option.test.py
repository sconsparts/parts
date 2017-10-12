Test.Summary = '''
This test the --log cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
Setup.Copy.FromTemplate('empty')

# note the --tc=null means we can set the target without issue of the tools complain
# that the can't setup correctly
t = Test.AddTestRun("good")
t.Command = "scons all --log --trace=logger_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/log_good1.gold'

t = Test.AddTestRun("good")
t.Command = "scons all --log=text --trace=logger_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/log_good1.gold'

t = Test.AddTestRun("good")
t.Command = "scons all --log=True --trace=logger_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/log_good1.gold'

t = Test.AddTestRun("good")
t.Command = "scons all --log=yes --trace=logger_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/log_good1.gold'

t = Test.AddTestRun("good")
t.Command = "scons all --log=1 --trace=logger_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/log_good1.gold'

t = Test.AddTestRun("good")
t.Command = "scons all --trace=logger_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/log_good2.gold'

t = Test.AddTestRun("good")
t.Command = "scons all --log=html --trace=logger_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/log_good3.gold'

t = Test.AddTestRun("good")
t.Command = "scons all --log=False --trace=logger_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/log_good4.gold'

t = Test.AddTestRun("good")
t.Command = "scons all --log=none --trace=logger_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/log_good4.gold'

t = Test.AddTestRun("good")
t.Command = "scons all --log=0 --trace=logger_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/log_good4.gold'

t = Test.AddTestRun("good")
t.Command = "scons all --log=no --trace=logger_option --tc=null --console-stream=none"
t.ReturnCode = 0
t.Streams.Debug = 'gold/log_good4.gold'

t = Test.AddTestRun("bad")
t.Command = "scons all --log=foo --trace=logger_option --tc=null --console-stream=none"
t.ReturnCode = 2
t.Streams.stderr = 'gold/log_bad1.gold'
