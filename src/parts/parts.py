
from __future__ import absolute_import, division, print_function

import parts.api as api
import parts.common as common
import parts.core as core
import parts.glb as glb
import parts.pnode as pnode
import parts.vcs as vcs
from SCons.Script.SConscript import SConsEnvironment


def Part_factory(arg1=None, parts_file=None, mode=[], vcs_type=vcs.null.null_t("#"), default=False,
                 append={}, prepend={}, create_sdk=True, package_group=None,
                 alias=None, name=None, *lst, **kw):
    ''' This  function acts a factory to help with Part creation.
    This way control over making a new Part or getting the existing Part
    can be better controled
    '''

    # handle common case:part(alias,file)
    if arg1 and parts_file is None:
        parts_file = arg1
    elif arg1 and parts_file and alias is None:
        alias = arg1

    tmp = glb.pnodes.Create(pnode.part.part, file=parts_file, mode=mode, vcs_t=vcs_type,
                            default=default, append=append, prepend=prepend,
                            create_sdk=create_sdk, package_group=package_group,
                            name=name, alias=alias, **kw)

    if tmp.isSetup:
        glb.engine._part_manager._add_part(tmp)

    return [tmp]


def SubPart_factory(env, arg1=None, parts_file=None, mode=[], vcs_type=None, default=False,
                    append={}, prepend={}, create_sdk=True, package_group=None, alias=None, name=None,
                    **kw):

    # handle common case:part(alias,file)
    if arg1 and parts_file is None:
        parts_file = arg1
    elif arg1 and parts_file and alias is None:
        alias = arg1

    return glb.engine._part_manager._define_sub_part(
        env,
        alias,
        env.subst(parts_file),
        mode,
        vcs_type,
        default,
        append,
        prepend,
        create_sdk,
        package_group,
        **kw
    )


# This is what we want to be setup in parts


# adding logic to Scons Enviroment object
SConsEnvironment.Part = SubPart_factory

# add configuartion varaible needed for part
api.register.add_variable('PART_BUILD_CONCEPT', 'build${ALIAS_SEPARATOR}', 'Namespace used to just build a given target')

api.register.add_variable('ALIAS_POSTFIX', '', ' ')
api.register.add_variable('ALIAS_PREFIX', '', '')

api.register.add_variable('PART_ALIAS_CONCEPT', 'alias${ALIAS_SEPARATOR}', 'Namespace to express building via an Alias target')
api.register.add_variable('PART_NAME_CONCEPT', 'name${ALIAS_SEPARATOR}',
                          'Namespace to express building via a Part Name and possible version')
api.register.add_variable('BUILD_DIR_ROOT', '#_build', 'Root directory for building a given build configuration/variant')
api.register.add_variable(
    'BUILD_DIR',
    '$BUILD_DIR_ROOT/${PART_SECTION}_${CONFIG}_${TARGET_PLATFORM}${"_"+TOOLCHAIN.replace(",","_") if TOOLCHAIN!="default" else ""}/$ALIAS',
    'Full path used to for building a given build configuration/variant')

api.register.add_variable('PARTS_SYS_DIR_ROOT', '#.parts.cache', 'Root directory for build data for the system')
api.register.add_variable(
    'PARTS_SYS_DIR',
    '$PARTS_SYS_DIR_ROOT/$PARTS_RUN_CSIG/${CONFIG}_${TARGET_PLATFORM}${"_"+TOOLCHAIN.replace(",","_") if TOOLCHAIN!="default" else ""}',
    'Full path used to for building a given build configuration/variant')


api.register.add_variable(
    'OUTOFTREE_BUILD_DIR', '$BUILD_DIR/__oot',
    'Full path used to for building a given build configuration/variant for files outside the part directory tree')
api.register.add_variable(
    'ROOT_BUILD_DIR', '$BUILD_DIR/__rt',
    'Full path used to for building a given build configuration/variant for files outside the part directory tree')

api.register.add_global_object('Part', Part_factory)
api.register.add_global_object('part', Part_factory)
