# Stub file to update env for ar tool

# import SCons.Tool.as as AS
AS = getattr(__import__('SCons.Tool.as', globals(), locals(), []).Tool, 'as')
import parts.tools.GnuCommon.binutils
import parts.tools.GnuCommon.common
import parts.tools.Common


def generate(env):
    parts.tools.GnuCommon.binutils.setup(env)
    ASPPSuffixes, ASSuffixes = list(AS.ASPPSuffixes), list(AS.ASSuffixes)
    if env['TARGET_OS'] == 'posix':
        try:
            AS.ASSuffixes.remove('.S')
        except ValueError:
            pass
        AS.ASPPSuffixes.append('.S')
    AS.generate(env)
    AS.ASPPSuffixes[:], AS.ASSuffixes[:] = ASPPSuffixes, ASSuffixes
    parts.tools.GnuCommon.common.makeStdBinutilsTool(env, 'AS', ['as'])


def exists(env):
    parts.tools.GnuCommon.binutils.setup(env)
    return AS.exists(env)

# vim: set et ts=4 sw=4 ai ft=python :
