import sys

Test.Summary = '''
This test checks that TarGzFile works and adds files to archive
'''

Setup.Copy.FromDirectory('test1')

t = Test.AddBuildRun('./lorem.tar.gz')
contains = ['lorem.txt', 'lorem3/lorem.txt', 'lorem2.txt']

content_tester = Testers.ZipContent(includes=contains)
t.ReturnCode = 0
t.Disk.File("lorem.tar.gz", exists=True, content=content_tester)
