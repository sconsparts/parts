Test.Summary = '''
Basic test for making sure sample works
'''
import sys

Setup.Copy.FromSample('unit_test2')

Test.AddBuildRun()
Test.AddUpdateCheck()
Test.AddOutOfDateCheck('utest::')
Test.AddCleanRun()
t = Test.AddBuildRun("utest::")
if sys.platform == 'win32':
    t.Disk.File("install/bin/engine.unit_tests-test_2.0.33.exe", exists=False)
    t.Disk.File("install/bin/engine.unit_tests-test2_2.0.33.exe", exists=False)
else:
    t.Disk.File("install/bin/engine.unit_tests-test_2.0.33", exists=False)
    t.Disk.File("install/bin/engine.unit_tests-test2_2.0.33", exists=False)

Test.AddUpdateCheck('utest::')

Test.AddOutOfDateCheck()
