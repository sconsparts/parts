Test.Summary = '''
Test the Setting PartVersion() api with various overrides and checks logic
'''

Setup.Copy.FromDirectory('base_test1')

# test that the default is set
tr = Test.AddBuildRun(options="--mode=TEST_DEFAULT --verbose=version",allow_warnings=True)
tr.Processes.Default.Streams.Warning = "gold/settingdefault.gold"
tr.Processes.Default.Streams.All = "gold/2.0.0set.gold"

tr = Test.AddBuildRun(options="--mode=TEST_DEFAULT,TEST_SUBST --verbose=version",allow_warnings=True)
tr.Processes.Default.Streams.Warning = "gold/settingdefault.gold"
tr.Processes.Default.Streams.All = "gold/2.0.0set.gold"
