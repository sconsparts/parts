Test.Summary='''
This test the --tool_chain cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
Setup.Copy.FromTemplate('empty')

t=Test.AddTestRun("good")
t.Command="scons all --tool-chain=null --trace=tool_chain_option --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/tc_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --toolchain=null --trace=tool_chain_option --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/tc_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --tc=null --trace=tool_chain_option --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/tc_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --tc=null_1.3.4 --trace=tool_chain_option --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/tc_good2.gold'

t=Test.AddTestRun("good")
t.Command="scons all --tc=null_1. --trace=tool_chain_option --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/tc_good3.gold'

t=Test.AddTestRun("good")
t.Command="scons all --tc=null_ --trace=tool_chain_option --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/tc_good4.gold'

t=Test.AddTestRun("good")
t.Command="scons all --tc=null,null --trace=tool_chain_option --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/tc_good5.gold'

t=Test.AddTestRun("good")
t.Command="scons all --tc=null_1,null --trace=tool_chain_option --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/tc_good6.gold'

t=Test.AddTestRun("good")
t.Command="scons all --tc=null_1,null_1 --trace=tool_chain_option --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/tc_good7.gold'

t=Test.AddTestRun("bad")
t.Command="scons all --tc=foo --trace=tool_chain_option --console-stream=none"
t.ReturnCode=2
t.Streams.Error='gold/tc_bad1.gold'
