
import parts.tools.GnuCommon.perl
import parts.api.output as output


def generate(env):
    """Add Builders and construction variables for gcc to an Environment."""
    # no builder yets.. add a PerlCommand()?

    # set up shell env for running compiler
    parts.tools.GnuCommon.perl.perl.MergeShellEnv(env)
    #api.output.print_msg("Configured Tool %s\t for version <%s> target <%s>"%('perl',env['PERL']['VERSION'],env['TARGET_PLATFORM']))


def exists(env):
    return parts.tools.GnuCommon.perl.perl.Exists(env)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
