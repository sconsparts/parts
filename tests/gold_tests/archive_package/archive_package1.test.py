import sys

Test.Summary='''
This test checks that the archive builder adds files to archive package from SConstruct.
Check for all the five type of builders
'''

Setup.Copy.FromDirectory('archive_package1')

Test.AddBuildRun('.')

