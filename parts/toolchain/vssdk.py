
def vssdk_setup(env,ver):
    env['VSSDK_VERSION']=ver

def resolve(env,version):
    func=lambda x : vssdk_setup(x,version)
    return [
                ('vssdk',func)
        ]