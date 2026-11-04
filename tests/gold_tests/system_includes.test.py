import shutil

Test.Summary = '''
Component(..., system=True) routes a dependency's include dirs through -isystem
instead of -I. The provider ships a header with an unused static function; the
consumer builds with -Wall -Werror. Compiled with -I that warning would fail
the build, so a clean build proves the headers came in as system includes
(-isystem), which suppresses warnings from them.
'''


def _has_cc():
    # the default toolchain (gcc on Linux, clang on macOS) must be present; the
    # build, not autest, resolves it, but skip cleanly if no compiler exists.
    return any(shutil.which(c) for c in ('gcc', 'clang', 'cc'))


Test.SkipUnless(
    Condition.Condition(lambda: _has_cc(), 'a C compiler (gcc/clang) is required to run this build')
)

Setup.Copy.FromDirectory('system_includes')

t = Test.AddBuildRun('all')
t.ReturnCode = 0
