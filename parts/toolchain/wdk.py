# defines tools chain wdk


def wdk_setup(env, ver):
    env['WDK_VERSION'] = ver


def resolve(env, version):

    func = lambda x: wdk_setup(x, version)
    return [
        ('wdk', func),
    ]
