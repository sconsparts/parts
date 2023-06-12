Test.Summary = '''
Test the Setting PartVersion() api with various overrides and checks logic
'''

Setup.Copy.FromDirectory('base_test1')

# test that the version is set with force logic
tr = Test.AddBuildRun(options="--mode=TEST_DEFAULT,TEST_FORCE --verbose=version",allow_warnings=True)
tr.Processes.Default.Streams.Warning = "gold/settingdefault.gold"
tr.Processes.Default.Streams.All = "gold/2.0.0set.gold"

# test that the version is set with force logic .. should error out with no version default being defined
tr = Test.AddBuildRun(options="--mode=TEST_FORCE --verbose=version",allow_warnings=True)
tr.Processes.Default.Streams.Error = "gold/versionnotset.gold"
tr.Processes.Default.ReturnCode = 2

# test that the version is set with force logic
tr = Test.AddBuildRun(options="--mode=TEST_FORCE,TEST_SETVERSION --verbose=version",allow_warnings=True)
tr.Processes.Default.Streams.All = "gold/overrideversion.gold"
