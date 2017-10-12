
def gas_setup(env, ver):
    if env.get('GCC_VERSION') is None:
        env['GCC_VERSION'] = ver


def resolve(env, version):
    del env
    func = lambda x: gas_setup(x, version)
    return [('gas', func)]
