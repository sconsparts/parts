


def clang_setup(env, ver):
    if env.get('AOCC_VERSION') is None:
        env['AOCC_VERSION'] = ver


def resolve(env, version):
    def func(x): return clang_setup(x, version)

    return [
        ('aocc', func),
        ('ar', None),
        ('gas', None),
        ('gnulink', None)
    ]
