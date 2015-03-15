Test.Summary='''
This test the --update cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
Setup.Copy.FromTemplate('empty')

# note the --tc=null means we can set the target without issue of the tools complain 
# that the can't setup correctly
t=Test.AddTestRun("good")
t.Command="scons all --update=auto --trace=update_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/update_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --vcs-update=auto --trace=update_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/update_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --trace=update_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/update_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --vcs-update=true --trace=update_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/update_good2.gold'

t=Test.AddTestRun("good")
t.Command="scons all --vcs-update=yes --trace=update_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/update_good2.gold'

t=Test.AddTestRun("good")
t.Command="scons all --vcs-update=t --trace=update_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/update_good2.gold'

t=Test.AddTestRun("good")
t.Command="scons all --vcs-update=all --trace=update_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/update_good2.gold'

t=Test.AddTestRun("good")
t.Command="scons all --vcs-update=False --trace=update_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/update_good3.gold'

t=Test.AddTestRun("good")
t.Command="scons all --vcs-update=no --trace=update_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/update_good3.gold'

t=Test.AddTestRun("good")
t.Command="scons all --vcs-update=f --trace=update_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/update_good3.gold'

t=Test.AddTestRun("good")
t.Command="scons all --vcs-update=none --trace=update_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/update_good3.gold'

t=Test.AddTestRun("good")
t.Command="scons all --vcs-update=joe,foo,boo --trace=update_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/update_good4.gold'
