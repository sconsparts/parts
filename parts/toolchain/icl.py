# defines tools chain icl ( as in the Intel Compiler windows)


def icl_setup(env, ver):
    env['INTELC_VERSION'] = ver


def resolve(env, version):
    func = lambda x: icl_setup(x, version)
    return [
        ('intelc', func)
    ]
