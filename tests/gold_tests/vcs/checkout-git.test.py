import os

Test.Summary = '''
This test checks that extract is OK from repository created on the fly
'''

Test.SkipUnless(
    Condition.HasProgram(
        program='git',
        msg='git must be present to create a git repository on-the-fly'
    )
)


# Setup
Test.Setup.Copy.FromDirectory('sc-git')
Test.Setup.Git.CreateRepository('git_compbar')
Test.Setup.Git.ImportDirectory('git_compbar', 'checkout-git', '.')

# Configuration of test run(s)
t = Test.AddBuildRun('all', 'GIT_PROTOCOL=file GIT_SERVER=$GIT_COMPBAR_GIT_PATH')
t.ReturnCode = 0
