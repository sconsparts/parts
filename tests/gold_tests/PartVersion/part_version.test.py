Test.Summary = '''
Test the Setting PartVersion() api with various overrides and checks logic
'''

Setup.Copy.FromDirectory('base_test1')

# The gold files below hold stdout only, so they compare against Streams.stdout.
# AuTest builds stream.all.txt by merging stdout and stderr from two reader
# threads, so a stderr line such as "Parts: Warning!:" lands at an unstable
# position in it. stderr is covered separately by the checks below.

# test that the default is set
tr = Test.AddBuildRun(options="--mode=TEST_DEFAULT --verbose=version",allow_warnings=True)
tr.Processes.Default.Streams.Warning = "gold/settingdefault.gold"
tr.Processes.Default.Streams.stdout = "gold/2.0.0set.gold"

tr = Test.AddBuildRun(options="--mode=TEST_DEFAULT,TEST_SUBST --verbose=version",allow_warnings=True)
tr.Processes.Default.Streams.Warning = "gold/settingdefault.gold"
tr.Processes.Default.Streams.stdout = "gold/2.0.0set.gold"
