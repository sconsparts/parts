# defines WiX tools chain


def wix_setup(env, ver):

    env['WIX_VERSION'] = ver


def resolve(env, version):

    def func(x): return wix_setup(x, version)
    return [
        ('wix', func),
    ]
