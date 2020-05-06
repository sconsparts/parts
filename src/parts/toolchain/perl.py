


def _setup(env, ver):
    env['PERL_VERSION'] = ver


def resolve(env, version):
    def func(x): return _setup(x, version)
    return [
        ('perl', func)
    ]
