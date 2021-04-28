Test.Summary = '''
Test the pattern object for cases of variant directory recursion
'''

Setup.Copy.FromDirectory('pattern1')

Test.AddBuildRun()
Test.AddCleanRun()
Test.AddBuildRun()
Test.AddUpdateCheck()



