import sys

Test.Summary=='''
This test checks that the archive builder adds files to archive package from SConstruct.
'''

Setup.Copy.FromDirectory('archive_package2')

Test.AddBuildRun('.')
