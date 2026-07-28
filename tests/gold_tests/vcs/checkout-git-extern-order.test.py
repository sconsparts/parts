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

# Get the sconstruct with two parts, one of which is has an extern part file
Test.Setup.Copy.FromDirectory('sc-git-extern')

# Setup part 1 repo
Test.Setup.Git.CreateRepository('git_compbar')
Test.Setup.Git.ImportDirectory('git_compbar', 'checkout-git', '.')

# Setup part 2 repo
Test.Setup.Git.CreateRepository('git_compbar2')
Test.Setup.Git.ImportDirectory('git_compbar2', 'checkout-git2', '.')

# Setup extern repo
Test.Setup.Git.CreateRepository('git_foobar')
Test.Setup.Git.ImportDirectory('git_foobar', 'checkout-git', '.')


# Configuration of test run(s)
t = Test.AddBuildRun('all', 'EXTERN_PART_PATH=$GIT_FOOBAR_GIT_PATH PART_PATH=$GIT_COMPBAR_GIT_PATH PART2_PATH=$GIT_COMPBAR2_GIT_PATH')
# t.ReturnCode = 0
t.Streams.stdout = 'gold/extern0.gold'
