from __future__ import absolute_import, division, print_function


def gxx_setup(env, ver):
    if env.get('GXX_VERSION') is None:
        env['GXX_VERSION'] = ver
    if env.get('GCC_VERSION') is None:
        env['GCC_VERSION'] = ver
    if env.get('BINUTILS_VERSION') is None and env['TARGET_PLATFORM'] == 'android':
        env['BINUTILS_VERSION'] = ver


def resolve(env, version):
    def func(x): return gxx_setup(x, version)

    host = env['HOST_PLATFORM']
    if host.OS == 'darwin' and not env['TARGET_PLATFORM'] == 'android':
        return [
            ('g++', func),
            ('gcc', func),
            ('ar', None),
            ('gas', None),
            ('applelink', None),
            ('lipo', None)
        ]

    else:
        return [
            ('g++', func),
            ('gcc', func),
            ('ar', None),
            ('gas', None),
            ('gnulink', None)
        ]
