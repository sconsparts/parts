def _setup(env,ver):
    env['PERL_VERSION']=ver

def resolve(env,version):
    func=lambda x : _setup(x,version)
    return [
                ('perl',func)
        ]