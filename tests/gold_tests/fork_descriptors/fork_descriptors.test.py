Test.Summary = '''
This is a test that checks that child processes don't inherit all our open file descriptors,
otherwise some files are kept open longer that we expected, sometimes leading to mysterious
failures (like a message from shell "bad interpreter: text file busy" when trying to execute
a file that was extracted from a tarball.

Test sequence should be:
    1) create a huge tarball (that would take significant time to unpack)
    2) start extracting it
    3) start some quick process ("sleep 0.1")
    4) start some long-running process (e.g. "sleep 5")
    5) wait for extract to complete
    6) try to shell-run extracted file while long-running process is alive

Note: that sequence should run in two threads, otherwise the data race might not happen.

If there are no bugs this should pass, otherwise there will be errors.

Test is applicable to POSIX only
'''

Test.SkipIf(Condition.IsPlatform('windows'))

Setup.Copy.FromDirectory('source')

t = Test.AddBuildRun('all -j2')
t.ReturnCode = 0
