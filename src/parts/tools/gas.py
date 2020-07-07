# Stub file to update env for ar tool


import parts.tools.Common
import parts.tools.GnuCommon.common

try:
    import SCons.Tool.asm as AS
except ImportError:
    AS = getattr(__import__('SCons.Tool.as', globals(), locals(), []).Tool, 'as')


def generate(env):
    parts.tools.GnuCommon.common.binutils.setup(env)
    ASPPSuffixes, ASSuffixes = list(AS.ASPPSuffixes), list(AS.ASSuffixes)
    if env['TARGET_OS'] in ('posix', 'android'):
        try:
            AS.ASSuffixes.remove('.S')
        except ValueError:
            pass
        AS.ASPPSuffixes.append('.S')
    AS.generate(env)
    AS.ASPPSuffixes[:], AS.ASSuffixes[:] = ASPPSuffixes, ASSuffixes

    env['AS'] = env.get('BINUTILS', {}).get('AS', env['AS'])
    env['AS'] = parts.tools.Common.toolvar(env['AS'], ('as',), env=env)


def exists(env):
    parts.tools.GnuCommon.common.binutils.setup(env)

    return AS.exists(env)

# vim: set et ts=4 sw=4 ai ft=python :
