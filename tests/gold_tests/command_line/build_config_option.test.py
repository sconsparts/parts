Test.Summary='''
This test the --build_config cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
Setup.Copy.FromTemplate('empty')

# note the --tc=null means we can set the target without issue of the tools complain 
# that the can't setup correctly
t=Test.AddTestRun("good")
t.Command="scons all --build-config=debug --trace=build_config_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/config_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --buildconfig=debug --trace=build_config_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/config_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --bldcfg=debug --trace=build_config_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/config_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --bcfg=debug --trace=build_config_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/config_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --cfg=debug --trace=build_config_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/config_good1.gold'

t=Test.AddTestRun("bad")
t.Command="scons all --cfg=fakeconfig --trace=build_config_option --tc=null --console-stream=none"
t.ReturnCode=2
t.Streams.Debug='gold/config_bad1t.gold'
t.Streams.Error='gold/config_bad1e.gold'

