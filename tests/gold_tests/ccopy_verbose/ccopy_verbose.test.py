import re

Test.Summary = '''
This is a test that verfies that the verbose flag can parse ccopy and that it is passed
onto the ccopy handler
'''

Setup.Copy.FromDirectory('source')

# No verbose setting, CCopy should not operate in verbose mode
Test.AddCleanRun('all')
t0 = Test.AddBuildRun('all')
t0.ReturnCode = 0
t0.Streams.stdout = 'gold/verbose_good0.gold'

# verbose=ccopy setting, CCopy should operate in verbose mode
Test.AddCleanRun('all')
t1 = Test.AddBuildRun('all', '--verbose=ccopy')
t1.ReturnCode = 0
t1.Streams.stdout = 'gold/verbose_good1.gold'

# verbose=all setting, CCopy should operate in verbose mode
Test.AddCleanRun('all')
t2 = Test.AddBuildRun('all', '--verbose=all')
t2.ReturnCode = 0
t2.Streams.stdout = 'gold/verbose_good1.gold'

# verbose=[not ccopy or all] setting, CCopy should not operate in verbose mode
Test.AddCleanRun('all')
t2 = Test.AddBuildRun('all', '--verbose=something')
t2.ReturnCode = 0
t2.Streams.stdout = 'gold/verbose_good0.gold'
