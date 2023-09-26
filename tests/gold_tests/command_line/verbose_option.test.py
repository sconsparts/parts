Test.Summary = '''
This test the --ccopy_logic cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
Setup.Copy.FromTemplate('empty')

# note the --tc=null means we can set the target without issue of the tools complain
# that the can't setup correctly

t = Test.AddBuildRun('all', '--verbose=ccopy --trace=verbose_option --tc=null --console-stream=none')
t.ReturnCode = 0
t.Streams.Debug = 'gold/verbose_good0.gold'

t = Test.AddBuildRun('all', '--verbose=ccopy,all --trace=verbose_option --tc=null --console-stream=none')
t.ReturnCode = 0
t.Streams.Debug = 'gold/verbose_good1.gold'
