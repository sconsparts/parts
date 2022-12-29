

import parts.glb as glb
from SCons.Script.SConscript import SConsEnvironment
from SCons.Environment import OverrideEnvironment 

from parts.core.states import GroupLogic

from . import output


def add_section(*, metasection, phases, target_mapping_logic=GroupLogic.DEFAULT):
    '''
    Called to add a new section type

    @param section The mapper object to add globally

    '''
    from parts.metasection.metasection import MetaSection
    from parts.metasection.sectiondefinition import SectionDefinition

    # check that this is a section object
    if not issubclass(metasection, MetaSection):
        output.warning_msg(f"{metasection} needs to derive from parts.pnode.metasection.MetaSection")

    # given all the checks are ok. Store a SectionDefinition
    section_def = SectionDefinition(
        metasection=metasection, 
        phaseinfo = phases,
        target_mapping_logic=target_mapping_logic
        )

    glb.section_definitions[section_def.Name] = section_def

    # add concept to known concept list for target processing later
    section_name = metasection.name
    for concept in metasection.concepts:
        # at the moment one concept to section.. may change that later
        if concept not in glb.known_concepts:
            output.verbose_msg(['section'], f"Mapping {concept} to section {section_name}")
            glb.known_concepts[concept] = section_name
        else:
            output.warning_msg(f"{concept} is already mapped to section {glb.known_concepts[concept]}..\
                \n Skipping mapping to section {section_name}")

    # bind the definition to the class
    metasection.definition = section_def


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
    if name not in glb.builders:
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
    settings.DefaultSettings().ListVariable(key, help=help, default=default, names=names, map=map, value=None, help_group=None)

def add_method(func,name:str=None):
    '''
    Add a method to the Environment(s) classes
    '''

    if not name:
        name = func.__name__

    setattr(SConsEnvironment, name, func)
    setattr(OverrideEnvironment, name, func)
    
