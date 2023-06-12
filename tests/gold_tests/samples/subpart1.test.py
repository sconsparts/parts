Test.Summary = '''
Basic test for making sure sample works
'''

Setup.Copy.FromSample('subpart1')

t = Test.AddBuildRun(allow_warnings=True) # todo! re-look at this for version warning
