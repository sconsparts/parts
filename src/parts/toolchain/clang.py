

def clang_setup(env, ver):
    if env.get('CLANG_VERSION') is None:
        env['CLANG_VERSION'] = ver


def resolve(env, version):
    def func(x): return clang_setup(x, version)

    host = env['HOST_PLATFORM']
    if host.OS == 'darwin' and not env['TARGET_PLATFORM'] == 'android':
        return [
            ('clang', func),
            ('ar', None),
            ('gas', None),
            ('applelink', None),
            ('lipo', None)
        ]

    else:
        return [
            ('clang', func),
            ('ar', None),
            ('gas', None),
            ('gnulink', None)
        ]
