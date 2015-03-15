Test.Summary='''
This test the --target_platform cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
Setup.Copy.FromTemplate('empty')

# note the --tc=null means we can set the target without issue of the tools complain 
# that the can't setup correctly
t=Test.AddTestRun("good")
t.Command="scons all --target-platform=win32-x86 --trace=target_platform_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/target_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --target=win32-x86 --trace=target_platform_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/target_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --target-platform=posix --trace=target_platform_option_os --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/target_good2.gold'

t=Test.AddTestRun("good")
t.Command="scons all --target-platform=x86 --trace=target_platform_option_arch --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/target_good3.gold'

t=Test.AddTestRun("good")
t.Command="scons all --target-platform=hp-ux-x86 --trace=target_platform_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/target_good4.gold'

t=Test.AddTestRun("good")
t.Command="scons all --target-platform=hp-ux --trace=target_platform_option_os --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/target_good5.gold'

t=Test.AddTestRun("good")
t.Command="scons all --tc=null --trace=target_platform_option --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/target_good6.gold'

# do runs with bad options
t = Test.AddTestRun("bad")
t.Command = "scons all --target-platform=fake-x86 --trace=target_platform_option --tc=null"
t.ReturnCode = 2
t.Streams.stderr = ['gold/target_bad1.scons23.gold', 'gold/target_bad1.scons21.gold']

t = Test.AddTestRun("bad")
t.Command = "scons all --target-platform=badval --trace=target_platform_option --tc=null"
t.ReturnCode = 2
t.Streams.stderr = ['gold/target_bad2.scons23.gold', 'gold/target_bad2.scons21.gold']

t = Test.AddTestRun("bad")
t.Command = "scons all --target-platform=darwin-z7000 --trace=target_platform_option --tc=null"
t.ReturnCode = 2
t.Streams.stderr = ['gold/target_bad3.scons23.gold', 'gold/target_bad3.scons21.gold']
