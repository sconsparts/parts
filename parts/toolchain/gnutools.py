
# defines tools chain for the general Gnu set( as needed for Intel Compiler posix or simular tools)


def _setup(env, ver):
    if env.get('GXX_VERSION') is None:
        env['GXX_VERSION'] = ver
    if env.get('GCC_VERSION') is None:
        env['GCC_VERSION'] = ver


def resolve(env, version):
    def func(x): return _setup(x, version)
    host = env['HOST_PLATFORM']
    if host.OS == 'darwin' and not env['TARGET_PLATFORM'] == 'android':
        return [
            ('g++', func, False),
            ('gcc', func, False),
            ('ar', None),
            ('gas', None),
            ('applelink', None),
            ('lipo', None)
        ]

    else:
        return [
            ('g++', func, False),
            ('gcc', func, False),
            ('ar', None),
            ('gas', None),
            ('gnulink', None)
        ]
