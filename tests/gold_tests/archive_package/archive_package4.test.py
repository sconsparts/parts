import sys

Test.Summary == '''
This test checks that the archive builder adds files to archive package from SConstruct.
This test is to check the normalization of packagetype given in control parts.
'''

Setup.Copy.FromDirectory('archive_package4')

Test.AddBuildRun('.')
