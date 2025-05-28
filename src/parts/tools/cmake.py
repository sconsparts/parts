import parts.tools.GnuCommon

def generate(env):
    """
    Add environment variables for the CMake build system
    """

    parts.tools.GnuCommon.cmake.MergeShellEnv(env)

def exists(env):
    return parts.tools.GnuCommon.cmake.Exists(env)
