######################################
### Intel compiler configurations default
######################################

from parts.config import *

def make_bool(obj):
    if obj is bool():
        return obj
    #assume string
    if obj.lower() == 'true':
        return True
    return False

def map_default_version(env):
    return env['INTELC_VERSION']

def post_process_func(env):
    # does not care if Intel Compiler version can or cannot
    # support given version. Compiler will complain if it can't
    try:
        ms_ver=float(env['MSVC_VERSION'])
    except:
        raise RuntimeError("You need to define mstools or compatible tool chain with Intel tool chain")
    
    env.AppendUnique(CCFLAGS=['/Qvc{0}'.format(ms_ver)])
    

    ## code coverage feature additions
    if make_bool(env.get('codecov',False)) == True:
        ver = env.Version(env['INTELC_VERSION'])
        env.AppendUnique(CCFLAGS=['/Z7'])
        if  ver < 11:
            env.AppendUnique(CCFLAGS=['/Qprof-genx'])
        elif 11 <= ver < 13:
            env.AppendUnique(CCFLAGS=['/Qprof-gen:srcpos'])
        else: # ver >= 13
            env.AppendUnique(CCFLAGS=['/Qcov-gen'])


config=configuration(map_default_version,post_process_func)

config.VersionRange("7-*",
                    append=ConfigValues(
                        CPPDEFINES=['WIN32','_WINDOWS'],
                        CCFLAGS=['/DINTELC_VERSION=$INTELC_VERSION']
                        )
                    )




