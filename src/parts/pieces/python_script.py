#################################################################
# PYTHON script builder
#################################################################

import parts.api as api
import SCons.Script
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment


def py_bld_str(target=None, source=None, env=None):
    return "Calling Script: " + str(source[0].srcnode().abspath)


def py_bld(target, source, env):
    import sys
    g = {}
    l = {}
    mod_name = source[0].srcnode().abspath[:-3].replace('.', '<dot>')
    m = sys.modules[mod_name]
    m.__dict__[env['__PYTHONSCRIPT_FUNC_']['build']](**env['__PYTHONSCRIPT_ARGS_'])
    print('Finished calling', source[0].srcnode().abspath)
    return None


def py_blde(target, source, env):
    import sys
    import importlib.machinery
    import importlib.util
    import os
    path, base = os.path.split(source[0].srcnode().abspath)

    # need to replace '.' with some other value else it will try to load a
    # non-existing parent module
    mod_name = source[0].srcnode().abspath[:-3].replace('.', '<dot>')

    spec = importlib.util.spec_from_file_location(mod_name, path)
    module = importlib.util.module_from_spec(spec)
    m = spec.loader.exec_module(module)

    headers = m.__dict__[env['__PYTHONSCRIPT_FUNC_']['emit']](**env['__PYTHONSCRIPT_ARGS_'])
    return (headers, source)


def PythonScript(env, file, emit_func='emit', build_func='build', func_args={}, **kw):
    f = {'emit': emit_func, 'build': build_func}
    return env._PyScriptBuilder_(target=[], source=file, __PYTHONSCRIPT_FUNC_=f, __PYTHONSCRIPT_ARGS_=func_args, **kw)


# adding logic to Scons Environment object
api.register.add_method(PythonScript)

api.register.add_builder('_PyScriptBuilder_', SCons.Script.Builder(
    action=SCons.Script.Action(py_bld, py_bld_str, varlist=['__PYTHONSCRIPT_FUNC_', '__PYTHONSCRIPT_ARGS_']),
    emitter=py_blde
))
