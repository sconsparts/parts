
from __future__ import absolute_import, division, print_function

import parts.api.output as output
import parts.tools.Common
import parts.tools.GnuCommon
import SCons.Tool
import SCons.Tool.mingw as mingw
import SCons.Util
from parts.tools.GnuCommon.android import GetLatestNDKAPI

cplusplus = __import__('c++', globals(), locals(), [])


# this are builders for making resources for mingw based builds on windows
res_action = SCons.Action.Action('$RCCOM', '$RCCOMSTR')

res_builder = SCons.Builder.Builder(action=res_action, suffix='.o',
                                    source_scanner=SCons.Tool.SourceFileScanner)
SCons.Tool.SourceFileScanner.add_scanner('.rc', SCons.Defaults.CScan)


def generate(env):
    """Add Builders and construction variables for g++ to an Environment."""
    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)

    # get the basic C++ flags (unix based stuff only??)
    cplusplus.generate(env)

    # set up shell env for running compiler
    parts.tools.GnuCommon.gxx.MergeShellEnv(env)

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

    env['CXX'] = parts.tools.Common.toolvar(env['GXX']['TOOL'], ('g++', 'gxx', 'gnu'), env=env)

    # platform specific settings
    # don't mess with these
    if env['PLATFORM'] == 'aix':
        env['SHCXXFLAGS'] = SCons.Util.CLVar('$CXXFLAGS -mminimal-toc')
        env['STATIC_AND_SHARED_OBJECTS_ARE_THE_SAME'] = 1
        env['SHOBJSUFFIX'] = '$OBJSUFFIX'
    else:
        env['SHOBJSUFFIX'] = '.pic.o'
        env['OBJSUFFIX'] = '.o'

    if env['TARGET_PLATFORM'] == 'android':
        env.SetDefault(ANDROID_API=GetLatestNDKAPI(env['GXX'].INSTALL_ROOT))
        env.SetDefault(ANDROID_STL='gnustl_shared')
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
    env['CXXVERSION'] = env['GXX']['VERSION']

    env.Append(**env['GXX'].get('APPENDS', {}))

 # fix this up so we can control its printing to screen better.
    #api.output.print_msg( "Configured Tool %s\t for version <%s> target <%s>"%('g++',env['GXX']['VERSION'],env['TARGET_PLATFORM']))


def exists(env):
    return parts.tools.GnuCommon.gxx.Exists(env)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
