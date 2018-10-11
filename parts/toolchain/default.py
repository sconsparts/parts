

import parts.load_module as load_module
import SCons.Tool
import platform

# this is a helper function to help with this code until we get a better solution created
# with the settings object


def test_tool(env, tool):
    return SCons.Tool.Tool(tool, toolpath=load_module.get_site_directories('tools')).Exists(env)


def resolve(env, version):
    host = env['HOST_PLATFORM']
    target = env['TARGET_PLATFORM']
    # native build on windows
    if host == 'win32' and target == 'win32':
        # prefer Intel compiler if they have it
        if test_tool(env, "intelc"):
            return [

                ('mstools', None),
                ('icl', None),
            ]
        else:
            if test_tool(env, "gcc") and not test_tool(env, "msvc"):
                # use gcc if it is the only tool installed
                return [
                    ('binutils', None),
                    ('gcc', None),
                ]
            return [
                ('cl', None)
            ]
    elif host == 'win32' and target == 'android':
        return [
            ('gxx', None)
        ]
    elif host.OS == 'darwin' and target == 'android':
        return [
            ('gxx', None)
        ]
    elif host == 'posix':
        # prefer intel tool if that have it
        if test_tool(env, "intelc"):
            return [
                ('gnutools', None),
                ('icc', None),
            ]
        else:
            return [
                ('gxx', None)
            ]
    elif host.OS == 'darwin':
        if test_tool(env, "intelc"):
            return [
                ('gnutools', None),
                ('icc', None),
            ]
        elif (platform.mac_ver()[0] >= env.Version("10.9.0")) and (test_tool(env, "clang")):
            return [
                ('clang', None)
            ]
        else:
            return [
                ('gxx', None)
            ]
    elif host.OS == 'sunos':
        return [
            ('gxx', None)
        ]
    else:
        print "Defaulting to Scons' default lookup"
        return [('default', {})]
