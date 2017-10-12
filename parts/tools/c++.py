# equivalent to "import SCons.Tool.c++ as cplusplus"
cplusplus = getattr(__import__('SCons.Tool.c++', globals(), locals(), []).Tool, 'c++')

# "inherit" almost everything except generate() from SCons.Tool.c++ module
for name in ('compilers', 'CXXSuffixes', 'iscplusplus', 'exists'):
    globals()[name] = getattr(cplusplus, name)

import parts.tools.Common


def generate(env):
    """
    Add Builders and construction variables for Visual Age C++ compilers
    to an Environment.
    """

    # We don't inherit this function because we want to set the settings via env.SetDefault(),
    # not via env[], thus allowing SConstruct to have some control over those variables

    import SCons.Tool
    import SCons.Tool.cc
    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)

    for suffix in CXXSuffixes:
        static_obj.add_action(suffix, SCons.Defaults.CXXAction)
        shared_obj.add_action(suffix, SCons.Defaults.ShCXXAction)
        static_obj.add_emitter(suffix, SCons.Defaults.StaticObjectEmitter)
        shared_obj.add_emitter(suffix, SCons.Defaults.SharedObjectEmitter)

    SCons.Tool.cc.add_common_cc_variables(env)

    env['CXX'] = parts.tools.Common.toolvar('c++', ('c++',), env=env)

    env.SetDefault(CXXFLAGS=SCons.Util.CLVar(''))
    #env['CXXCOM']     = '$CXX -o $TARGET -c $CXXFLAGS $CCFLAGS $_CCCOMCOM $SOURCES'
    env.SetDefault(CXXCOM='${TEMPFILE("$CXX -o $TARGET -c $CXXFLAGS $CCFLAGS $_CCCOMCOM $SOURCES $CCARCHFLAGS")}')
    env.SetDefault(SHCXX='$CXX')
    env.SetDefault(SHCXXFLAGS=SCons.Util.CLVar('$CXXFLAGS'))
    #env['SHCXXCOM']   = '$SHCXX -o $TARGET -c $SHCXXFLAGS $SHCCFLAGS $_CCCOMCOM $SOURCES'
    env.SetDefault(SHCXXCOM='${TEMPFILE("$SHCXX -o $TARGET -c $SHCXXFLAGS $SHCCFLAGS $_CCCOMCOM $SOURCES $CCARCHFLAGS")}')

    env.SetDefault(CPPDEFPREFIX='-D')
    env.SetDefault(CPPDEFSUFFIX='')
    env.SetDefault(INCPREFIX='-I')
    env.SetDefault(INCSUFFIX='')
    env.SetDefault(SHOBJSUFFIX='.os')
    env.SetDefault(OBJSUFFIX='.o')
    env.SetDefault(STATIC_AND_SHARED_OBJECTS_ARE_THE_SAME=0)

    env.SetDefault(CXXFILESUFFIX='.cc')

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
