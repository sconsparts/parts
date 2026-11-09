import re

Test.Summary = '''
Each group alias of a unit_test section must hold the alias of each build
section that the unit_test section depends on with the default requirements,
so that the run of a group waits for it. Dry runs only, so this test also runs
where the real runs in unittest_depends_install and
unittest_depends_install_classic are skipped.
'''

Setup.Copy.FromDirectory('test_depends_install')

# --tree=prune prints a node again as "+-[name]"
depends_on_a = r'\+-\[?build::alias::A\]?$'

# before the fix, only utest::alias::B held A's build alias, and the run alias
# of a group does not depend on it
t = Test.AddBuildRun('run_utest::alias::B::test', '-n --tree=prune')
t.Streams.stdout = Testers.ContainsExpression(
    depends_on_a, 'the run of group test must depend on build::alias::A')
# the fix must not make the run of one group depend on the section alias, which
# holds every group
t.Streams.stdout += Testers.ExcludesExpression(
    r'utest::alias::B::other', 'the run of group test must not depend on group other')

# every group gets it. Both group aliases are checked in one process: the order
# of the set of groups changes between processes, so a mapping onto only the
# first group could pass separate runs.
def group_depends_on_a(group):
    # the tree of the group alias (its lines are indented), down to build::alias::A
    return Testers.ContainsExpression(
        rf'^\+-utest::alias::B::{group}$(?:\n  .*)*?\n  .*\+-\[?build::alias::A\]?$',
        f'group {group} must depend on build::alias::A', reflags=re.MULTILINE)


t = Test.AddBuildRun('utest::alias::B::test', 'utest::alias::B::other -n --tree=prune')
t.Streams.stdout = group_depends_on_a('test')
t.Streams.stdout += group_depends_on_a('other')

# env.UnitTest(): utest::alias::C::test -> build::alias::C -> build::alias::A
t = Test.AddBuildRun('run_utest::alias::C::test', '-n --tree=prune')
t.Streams.stdout = Testers.ContainsExpression(
    depends_on_a, 'the run of the env.UnitTest() test must depend on build::alias::A')
