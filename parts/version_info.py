from parts_version import _PARTS_VERSION


def print_version():
    print parts_version_text()


def parts_version_text():
    return 'Parts extension for SCons, Version ' + _PARTS_VERSION


def parts_version_text_env(env):
    return parts_version_text()


def is_parts_version_beta():
    if 'beta' in _PARTS_VERSION.lower():
        return True
    return False


def is_parts_version_beta_env(env):
    return is_parts_version_beta()


def PartsExtensionVersion():
    import version
    return version.version(_PARTS_VERSION)


def PartsExtensionVersion_env(env):
    return PartsExtensionVersion()

# currently this allow us to load Parts without issues of SCons being loaded
try:
    import api

    # add to parts file as globals
    api.register.add_global_parts_object('PartVersionString', parts_version_text)
    api.register.add_global_parts_object('IsPartsExtensionVersionBeta', is_parts_version_beta)
    api.register.add_global_parts_object('PartsExtensionVersion', PartsExtensionVersion)

    # add to Sconsctruct as globals
    api.register.add_global_object('PartVersionString', parts_version_text)
    api.register.add_global_object('IsPartsExtensionVersionBeta', is_parts_version_beta)
    api.register.add_global_object('PartsExtensionVersion', PartsExtensionVersion)

    # This is what we want to be setup in parts
    from SCons.Script.SConscript import SConsEnvironment

    # adding logic to Scons Enviroment object
    SConsEnvironment.PartVersionString = parts_version_text_env
    SConsEnvironment.IsPartsExtensionVersionBeta = is_parts_version_beta_env
    SConsEnvironment.PartsExtensionVersion = PartsExtensionVersion_env
except:
    pass
