Test.Summary = '''
This tests that the mapping of custom data work as expected in classic format, when mapped to public area
'''
Setup.Copy.FromDirectory('depends_platform_match')

t = Test.AddBuildRun('all', '--trace=component')
t.Streams.stdout = 'gold/depends_platform_match.gold'
