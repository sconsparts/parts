Test.Summary = '''
Test the Setting PartVersion() api with various overrides and checks logic
'''

Setup.Copy.FromDirectory('base_test1')

# has default but version not set, so act as Default logic
tr = Test.AddBuildRun(options="--mode=TEST_DEFAULT,TEST_VERIFY --verbose=version",allow_warnings=True,extra="TEST_DEFAULT,TEST_VERIFY")
tr.Processes.Default.Streams.Warning = "gold/settingdefault.gold"
tr.Processes.Default.Streams.All = "gold/2.0.0set.gold"

# test that the version is set with verify logic this should error out as the miss match
tr = Test.AddBuildRun(options="--mode=TEST_SETVERSION,TEST_VERIFY --verbose=version",allow_warnings=True, extra="TEST_SETVERSION,TEST_VERIFY")
tr.Processes.Default.Streams.Error = "gold/verify_error.gold"
tr.Processes.Default.ReturnCode = 2

# test verify logic but we have no default version, should be ignored
tr = Test.AddBuildRun(options="--mode=TEST_VERIFY --verbose=version",allow_warnings=False,extra="TEST_VERIFY")
tr.Processes.Default.Streams.Verbose = "gold/verify_ignore.gold"

# has default but version not set, so act as Default logic
tr = Test.AddBuildRun(options="--mode=TEST_DEFAULT,TEST_STRICTVERIFY --verbose=version",allow_warnings=True,extra="TEST_DEFAULT,TEST_STRICTVERIFY")
tr.Processes.Default.Streams.Warning = "gold/settingdefault.gold"
tr.Processes.Default.Streams.All = "gold/2.0.0set.gold"

# test that the version is set with verify logic this should error out as the miss match
tr = Test.AddBuildRun(options="--mode=TEST_SETVERSION,TEST_STRICTVERIFY --verbose=version",allow_warnings=True, extra="TEST_SETVERSION,TEST_STRICTVERIFY")
tr.Processes.Default.Streams.Error = "gold/verify_error.gold"
tr.Processes.Default.ReturnCode = 2

# test verify logic but we have no default version, should be error out
tr = Test.AddBuildRun(options="--mode=TEST_STRICTVERIFY --verbose=version",allow_warnings=True, extra="TEST_STRICTVERIFY")
tr.Processes.Default.Streams.Error = "gold/verify_nodefault_error.gold"
tr.Processes.Default.ReturnCode = 2

# test verify logic but we have no default version, should be error out
tr = Test.AddBuildRun(options="--mode=TEST_VERIFY,TEST_MATCH --verbose=version",allow_warnings=True, extra="TEST_VERIFY,TEST_MATCH")
tr.Processes.Default.Streams.All = "gold/verify_match_msg.gold"


# test verify logic but we have no default version, should be error out
tr = Test.AddBuildRun(options="--mode=TEST_STRICTVERIFY,TEST_MATCH --verbose=version",allow_warnings=True, extra="TEST_STRICTVERIFY,TEST_MATCH")
tr.Processes.Default.Streams.All = "gold/verify_match_msg.gold"

# with subst logic

# has default but version not set, so act as Default logic
tr = Test.AddBuildRun(options="--mode=TEST_DEFAULT,TEST_VERIFY,TEST_SUBST --verbose=version",allow_warnings=True,extra="TEST_DEFAULT,TEST_VERIFY")
tr.Processes.Default.Streams.Warning = "gold/settingdefault.gold"
tr.Processes.Default.Streams.All = "gold/2.0.0set.gold"

# test that the version is set with verify logic this should error out as the miss match
tr = Test.AddBuildRun(options="--mode=TEST_SETVERSION,TEST_VERIFY,TEST_SUBST --verbose=version",allow_warnings=True, extra="TEST_SETVERSION,TEST_VERIFY")
tr.Processes.Default.Streams.Error = "gold/verify_error.gold"
tr.Processes.Default.ReturnCode = 2

# test verify logic but we have no default version, should be ignored
tr = Test.AddBuildRun(options="--mode=TEST_VERIFY,TEST_SUBST --verbose=version",allow_warnings=False,extra="TEST_VERIFY")
tr.Processes.Default.Streams.Verbose = "gold/verify_ignore.gold"

# has default but version not set, so act as Default logic
tr = Test.AddBuildRun(options="--mode=TEST_DEFAULT,TEST_STRICTVERIFY,TEST_SUBST --verbose=version",allow_warnings=True,extra="TEST_DEFAULT,TEST_STRICTVERIFY")
tr.Processes.Default.Streams.Warning = "gold/settingdefault.gold"
tr.Processes.Default.Streams.All = "gold/2.0.0set.gold"

# test that the version is set with verify logic this should error out as the miss match
tr = Test.AddBuildRun(options="--mode=TEST_SETVERSION,TEST_STRICTVERIFY,TEST_SUBST --verbose=version",allow_warnings=True, extra="TEST_SETVERSION,TEST_STRICTVERIFY")
tr.Processes.Default.Streams.Error = "gold/verify_error.gold"
tr.Processes.Default.ReturnCode = 2

# test verify logic but we have no default version, should be error out
tr = Test.AddBuildRun(options="--mode=TEST_STRICTVERIFY,TEST_SUBST --verbose=version",allow_warnings=True, extra="TEST_STRICTVERIFY")
tr.Processes.Default.Streams.Error = "gold/verify_nodefault_error.gold"
tr.Processes.Default.ReturnCode = 2

# test verify logic but we have no default version, should be error out
tr = Test.AddBuildRun(options="--mode=TEST_VERIFY,TEST_MATCH,TEST_SUBST --verbose=version",allow_warnings=True, extra="TEST_VERIFY,TEST_MATCH")
tr.Processes.Default.Streams.All = "gold/verify_match_msg.gold"


# test verify logic but we have no default version, should be error out
tr = Test.AddBuildRun(options="--mode=TEST_STRICTVERIFY,TEST_MATCH,TEST_SUBST --verbose=version",allow_warnings=True, extra="TEST_STRICTVERIFY,TEST_MATCH")
tr.Processes.Default.Streams.All = "gold/verify_match_msg.gold"