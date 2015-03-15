"""
Stub tool file for binutils tool chain. It has to be here for correct tool chain detection.
"""

import parts.tools.GnuCommon

def generate(env):
    """This function must be present in a tool .py file.
       For the ld tool it is implemented as a stub because ld executable is not called directly but
       only by gcc/g++ driver."""
    pass

def exists(env):
    return parts.tools.GnuCommon.binutils.Exists(env)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:


