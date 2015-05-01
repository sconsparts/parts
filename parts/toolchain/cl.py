# defines tools chain cl ( as in microsft CL)


def cl_setup(env,ver):
    
    env['MSVC_VERSION']=ver
    env['MSVS_VERSION']=ver
    env['MSVC_INSTALL_ROOT']=None


def resolve(env,version):
    
    func=lambda x : cl_setup(x,version)
    return [
                ('msvc',func),
                ('mslink',func),
                ('masm',func),
                ('mslib',func),
                ('midl',func),
                ('signfile',None)
            ]