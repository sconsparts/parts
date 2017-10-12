# defines WiX tools chain


def wix_setup(env, ver):

    env['WIX_VERSION'] = ver


def resolve(env, version):

    func = lambda x: wix_setup(x, version)
    return [
        ('wix', func),
    ]
