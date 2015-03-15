
"""
Setup of the SDK for MS.
This is different from SCons in the Scons will try to load this all the time

I will only load if requested. This will prevent the user from getting the SDK
from overrideing the basic setting if they did not want it to. Ideally the tool
chains in Parts will allow easy control to add or not add this tool.

Note this "Tool" is more of a library. it just adds paths, no builders

"""

import parts.tools.MSCommon.sdk
from parts.tools.MSCommon import mssdk
import parts.api.output as output
import parts.tools.Common

def generate(env):
    """Add construction variables for an MS SDK to an Environment."""

    mssdk.MergeShellEnv(env)
    #api.output.print_msg("Configured Tool %s\t for version <%s> target <%s>"%('mssdk',env['MSVC']['VERSION'],env['TARGET_PLATFORM']))
    return

def exists(env,version=None):
    return msvc.Exists(env)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
