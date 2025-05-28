

def emsdk_setup(env, ver):
    if env.get('EMSDK_VERSION') is None:
        env['EMSDK_VERSION'] = ver

def resolve(env, version):
    def func(x): return emsdk_setup(x, version)

    return [
        ('emsdk', func),
        ('ar', None),
        ('gas', None),
        ('gnulink', None)
    ]
