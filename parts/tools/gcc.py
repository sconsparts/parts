from __future__ import absolute_import, division, print_function

import parts.api.output as output
import parts.tools.cc
import parts.tools.Common
import parts.tools.GnuCommon
from parts.tools.GnuCommon.android import GetLatestNDKAPI

import SCons.Tool.cc
import SCons.Tool.mingw as mingw
import SCons.Util


def generate(env):
    """Add Builders and construction variables for gcc to an Environment."""
    parts.tools.cc.generate(env)

    # set up shell env for running compiler
    parts.tools.GnuCommon.gcc.MergeShellEnv(env)
    # does the tool define tweaks to the bnutils.. if so set these "gloally"
    try:
        env['OBJCOPY'] = env['GXX']['OBJCOPY']
    except KeyError:
        pass
    try:
        env['AR'] = env['GXX']['AR']
    except KeyError:
        pass
    try:
        env['LD'] = env['GXX']['LD']
    except KeyError:
        pass

    env['CC'] = parts.tools.Common.toolvar(env['GCC']['TOOL'], ('gcc', 'gnu'), env=env)

   # this setting is what SCons has.. It seem odd, I thought cygwin handled -fpic fine
    if env['PLATFORM'] in ['cygwin', 'win32']:
        env['SHCCFLAGS'] = SCons.Util.CLVar('$CCFLAGS')
    else:
        env['SHCCFLAGS'] = SCons.Util.CLVar('$CCFLAGS -fPIC')

    if env['TARGET_PLATFORM'] == 'android':
        env.SetDefault(ANDROID_API=GetLatestNDKAPI(env['GCC'].INSTALL_ROOT))
    elif env['TARGET_PLATFORM'] == 'win32':
        # set some value for the mingw build
        # note on this side we have export libs

        # resource builder
        env['WIN32DEFPREFIX'] = ''
        env['WIN32DEFSUFFIX'] = '.def'
        env['WINDOWSDEFPREFIX'] = '${WIN32DEFPREFIX}'
        env['WINDOWSDEFSUFFIX'] = '${WIN32DEFSUFFIX}'

        env['SHOBJSUFFIX'] = '.o'
        env['STATIC_AND_SHARED_OBJECTS_ARE_THE_SAME'] = 1

        env['RC'] = 'windres'
        env['RCFLAGS'] = SCons.Util.CLVar('')
        env['RCINCFLAGS'] = '$( ${_concat(RCINCPREFIX, CPPPATH, RCINCSUFFIX, __env__, RDirs, TARGET, SOURCE)} $)'
        env['RCINCPREFIX'] = '--include-dir '
        env['RCINCSUFFIX'] = ''
        env['RCCOM'] = '$RC $_CPPDEFFLAGS $RCINCFLAGS ${RCINCPREFIX} ${SOURCE.dir} $RCFLAGS -i $SOURCE -o $TARGET'
        env['BUILDERS']['RES'] = mingw.res_builder

    # Backward compatiblity
    env['CCVERSION'] = env['GCC']['VERSION']

    env['SHOBJSUFFIX'] = '.pic.o'
    env['OBJSUFFIX'] = '.o'

    env.Append(**env['GCC'].get('APPENDS', {}))

 # fix this up so we can control its printing to screen better.
    #api.output.print_msg("Configured Tool %s\t for version <%s> target <%s>"%('gcc',env['GCC']['VERSION'],env['TARGET_PLATFORM']))


def exists(env):
    return parts.tools.GnuCommon.gcc.Exists(env)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
