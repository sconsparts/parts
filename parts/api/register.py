
from .. import glb
import output


import SCons.Script


def add_section(section):
    '''
    Called to add a new section type

    @param section The mapper object to add globally

    '''
    glb.sections.add(section)


def add_mapper(mapper):
    '''
    Called to add a new mapper object

    @param mapper The mapper object to add globally

    '''
    glb.mappers[mapper.name] = mapper


def add_global_parts_object(key, object, map_env=False):
    '''
    Called to add a function or object at a global "part file" scope

    @param key The value the object will be seen as by the user
    @param object The object we want to add
    @param map_env Map the object with env instance that will passed to the user.

    If map_env is true the object as to be a class. the setup code will create an
    instance that will have the __init__ passed env as the only argument, for it to store
    when the calls an API or __call__ method.
    '''
    if map_env:
        glb.parts_objs_env[key] = object
    else:
        glb.parts_objs[key] = object


def add_global_object(key, object):
    '''
    Called to add an object at a global Sconstruct level

    @param key The value the object will be seen as by the user
    @param object The object we want to add
    '''
    glb.globals[key] = object


def add_builder(name, builder):
    try:
        builder.name
    except AttributeError:
        builder.name = name
    if (name in glb.builders) == False:
        glb.builders[name] = builder
    else:
        output.warning_msg('Builder "{0}" was already defined. Ignoring new definition.'.format(name), show_stack=False)


def add_variable(key, default, help, validator=None, converter=None):
    '''Generic variable addition'''
    from .. import settings
    settings.DefaultSettings().AddVariable(key, help=help, default=default, validator=validator,
                                           converter=converter, value=None, help_group=None)


def add_bool_variable(key, default, help):
    '''Generic variable addition'''
    from .. import settings
    settings.DefaultSettings().BoolVariable(key, help=help, default=default, value=None, help_group=None)


def add_enum_variable(key, default, help, allowed_values, map={}, ignorecase=1):
    '''Generic variable addition'''
    from .. import settings
    settings.DefaultSettings().EnumVariable(key, help=help, default=default, allowed_values=allowed_values,
                                            map=map, ignorecase=ignorecase, value=None, help_group=None)


def add_list_variable(key, default, help, names=[], map={}):
    '''Generic variable addition'''
    from .. import settings
    from .. import Variables
    settings.DefaultSettings().ListVariable(key, help=help, default=default, names=names, map=map, value=None, help_group=None)
