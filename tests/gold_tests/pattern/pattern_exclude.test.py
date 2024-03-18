Test.Summary = '''
Test the pattern object for not scanning excluded directories
'''

Setup.Copy.FromDirectory('pattern_exclude')

tr = Test.AddBuildRun("all --verbose=pattern")
tr.Processes.Default.Streams.All.Content = Testers.ExcludesExpression(r'[/\\]yes[/\\]no', "The pattern should not contain any files with 'no' in the name")



