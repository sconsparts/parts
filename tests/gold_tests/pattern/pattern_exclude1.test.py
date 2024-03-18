Test.Summary = '''
Test the pattern object for not scanning excluded directories, check for items that end with a pattern
In this case, we want the pattern to recursively scan the directory even if the exclude pattern is a "match" for the directory name
'''

Setup.Copy.FromDirectory('pattern_exclude1')

tr = Test.AddBuildRun("all --verbose=pattern")
tr.Processes.Default.Streams.All.Content = Testers.ExcludesExpression(r'[/\\]yes[/\\]no', "The pattern should not contain any files with 'no' in the name")



