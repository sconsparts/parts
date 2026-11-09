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

# up to date before the change, so the rebuild below is the header's doing
Test.AddUpdateCheck('all')

# A change to the provider's header has to rebuild the consumer. The consumer
# finds the header through SYSCPPPATH (-isystem), so unless the C scanner
# searches SYSCPPPATH too, the header never becomes a dependency of main.o.
t = Test.AddTestRun('change-provider-header', "Change the provider's header")
t.Command = "echo '#define PROVIDER_CHANGED 1' >> provider/inc.h"
t.ReturnCode = 0

t = Test.AddBuildRun('all', extra='-after-header-change')
t.ReturnCode = 0
t.Streams.All.Content = Testers.ContainsExpression(
    r'\s-c\s.*main\.c\b', 'the consumer compiles main.c again')
