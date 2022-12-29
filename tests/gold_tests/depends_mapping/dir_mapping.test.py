Test.Summary = '''
Test the basic directory output targets work as expected
'''
Setup.Copy.FromDirectory('dir_mapping')

t = Test.AddBuildRun('all')

# everything should be up-to-date
Test.AddUpdateCheck('all')
