from typing import Union, List, cast, Sequence, TypeVar

import parts.api as api
import parts.api.requirement  # this is need to have some data set at start correctly
import parts.common as common
import parts.core.util as util
import parts.core.builders as builders
import parts.dependent_ref as dependent_ref
import parts.errors as errors
import parts.functors as functors
import parts.glb as glb
import parts.part_ref as part_ref
import parts.target_type as target_type
import parts.version as version
import SCons.Script
import parts.requirement as requirement
from SCons.Debug import logInstanceCreation
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment


def Component(env, name, version_range=None, requires: requirement.REQ = None, section="build", optional: bool = False) -> dependent_ref.dependent_ref:

    # Resolve value in the name string is any
    name = env.subst(name)
    # if this start with alias. we want to us it not name::
    # If it does not start with name we want to add it
    if name.startswith("name::") == False and name.startswith("alias::") == False:
        name = 'name::{0}'.format(name)

    # make it a target
    trg = target_type.target_type(name)

    # debug/trace
    #api.output.trace_msgf(['component'], "target value: {}\n {}", trg, trg.__dict__)

    # get pobj that called this mapping of a component
    pobj = glb.engine._part_manager._from_env(env)
    api.output.trace_msg(
        ['component'],
        "Mapping defined for:\n  target: {target}\n with part:\n  name:{name}\n  section:{section}\n  ID={ID}".format(
            target=trg,
            name=pobj.Name,
            section=section,
            ID=pobj.ID)
    )

    # compatibility with 0.15.8 and older
    if not requires:
        requires = requirement.REQ.DEFAULT

    # get any local space that was set
    localspace = pobj.Uses

    if localspace:
        # TODO clean up this message
        api.output.trace_msg(
            ['component'],
            "Localspace mapping space was defined! {}".format(localspace)
        )

    # try to auto select version
    # check to see if this is a subpart and if so we want to
    # auto define the version range to be that of the parent
    # this allow subparts to easily depend on there part "group"

    if version_range is None:
        # check to see if the name we dependon match
        # TODO validate this test....
        if pobj.Root.Name == trg.Name:
            version_range = version.version_range(pobj.Version)
    else:
        # we have a version range define...
        # turn it in to an version_range object
        version_range = version.version_range(env.subst(version_range))

    # set the target value
    if ('target' in trg.Properties) == False:  # ['target','target-platform','target_platform']
        api.output.trace_msg(
            ['component'],
            "Defining default platform_match mapping of:", env['TARGET_PLATFORM'])
        trg.Properties['platform_match'] = env['TARGET_PLATFORM']
    else:
        api.output.trace_msg(
            ['component'],
            "Target defined platform_match mapping of:", trg.Properties['target'])

    # set the version value
    if version_range:
        if trg.Properties.get('version'):
            api.output.trace_msg(
                ['component'],
                "Overriding version properties of\n  {old} \n with\n  {new}".format(
                    old=trg.Properties.get('version'),
                    new=version_range
                )
            )
        trg.Properties['version'] = version_range
    elif ('version' in trg.Properties) == False:
        api.output.trace_msg(
            ['component'],
            "Defining default version range mapping of '*'")
        trg.Properties['version'] = '*'

    # Set the configuration to try to match
    if ('config' in trg.Properties) == False:
        config = str(env['CONFIG'])
        api.output.trace_msg(['component'], "Defining default config mapping of:", config)
        trg.Properties['config'] = str(env['CONFIG'])
    else:
        api.output.trace_msg(['component'], "Target defined config mapping of:", trg.Properties['config'])

    return dependent_ref.dependent_ref(part_ref.PartRef(trg, localspace), section, requires, optional)


class ComponentEnv:

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, name, version_range=None, requires=None, section="build", optional: bool = False):
        return self.env.Component(name, version_range, requires, section, optional)


def depends_on_classic(env, depends: Union[dependent_ref.dependent_ref, List[dependent_ref.dependent_ref]]):
    '''
    This form requires that all dependance get defined by a "mapper" object.
    This allow for delay processing that is required as at any given time this
    is call we don't really know all the Parts object that could exist. So we leave
    a "calling" card for what we want to find in this place.
    '''
    errors.SetPartStackFrameInfo()

    sobj = glb.engine._part_manager.section_from_env(env)
    if sobj is None:
        return

    api.output.verbose_msg('dependson', "Mapping data to {sobj.ID}")
    # depends that get passed on
    if util.isList(depends) == False:
        depends = [cast(dependent_ref.dependent_ref, depends)]

    for comp in cast(List[dependent_ref.dependent_ref], depends):
        # quick error check
        if sobj.Part.Name == comp.PartRef.Target.Name and sobj.Name == comp.SectionName:
            api.output.warning_msg("Part depends on with itself")
            api.output.print_msg("Skipping the definition of dependence to SCons")
            continue
        api.output.verbose_msg('dependson', " Component", comp.PartRef.Target.Name)

        # we have something to map. To help with the newer logic we add a value to the section
        # we would be mapping to, so it is known we have stuff here
        comp.isClassicallyMapped = True

        for r in comp.Requires:
            ## import logic
            # always map to namespace
            # split the name so we can make an sub spaces
            tmp = comp.PartRef.Target.Name.split('.')
            # get the space in the environment
            try:
                tmpspace = env['DEPENDS']
            except KeyError:
                tmpspace = common.namespace()
                env['DEPENDS'] = tmpspace

            for i in tmp:
                try:
                    tmpspace = tmpspace[i]
                except KeyError:
                    tmpspace[i] = common.namespace()
                    tmpspace = tmpspace[i]
            map_val = r.value_mapper(comp.PartRef.Target, comp.SectionName, comp.isOptional)
            # builders.imports.map_imports_depends(env,map_val)
            tmpspace[r.key] = map_val

            # if this is a list and is not private we map to global space via an append
            if r.is_public and r.is_list:
                # map virtual depend node
                api.output.verbose_msg('dependson', "  Global list", r.key, map_val)
                env.AppendUnique(
                    delete_existing=True,
                    **{r.key: [map_val]}
                )

            elif r.is_public:
                api.output.verbose_msg('dependson', "  Global value", r.key, map_val)
                if r.key in env:
                    env[r.key] = [env[r.key], map_val]
                else:
                    env[r.key] = map_val
            # export logic
            # if this is not internal we add to the current component export table
            if r.is_internal == False:
                api.output.verbose_msg('dependson', "  exporting", r.key, map_val)
                if r.key not in sobj.Exports and r.is_list:
                    sobj.Exports[r.key] = [[]]

                if r.is_list:
                    sobj.Exports[r.key] = common.extend_unique(sobj.Exports[r.key], [[map_val]])
                else:
                    sobj.Exports[r.key] = map_val
                api.output.verbose_msg('dependson', "  Exported values", sobj.Exports[r.key])

    errors.ResetPartStackFrameInfo()


def depends_on(env, depends: Union[str, Component, Sequence[Union[str , Component]]]) -> None:
    '''
    This is the generic DependsOn function. There are a section version which are more optimized as they don't
    need to worry about backward compatibility. This version has to do use mappers to allow for delayed resolution
    of values.
    '''
    # check that we are calling this as intended .. ie not in a section callback function
    # env???

    if glb.processing_sections:
        output.error_msg("DependsOn cannot be called with a Section callback function")
    # do we have anything?
    if not depends:
        return

    # need check that we are only be called while the part is being read.
    # in the new sections we don't want this to be called when we are processing a section
    # We want to make sure all known depends are define after the part files are read in.
    # todo...

    depends_list = []
    # make this a list if it is not already
    depends = common.make_list(depends)

    # make any string a component object
    for i in depends:
        if util.isString(i):
            depends_list.append(Component(env, i))
        else:
            depends_list.append(i)

    ########################################
    ## set what we depend on
    # this will be resolved latter when we process the Parts objects

    # Get the part object mapped to this environment
    sobj = glb.engine._part_manager.section_from_env(env)
    if sobj is None:
        # should not happen.. need some more testing to make sure we can define a clever case
        # todo make test case for this
        api.output.error_msg("Unexpected! DependsOn called and no defining secion was found! Please report this issue.")


    # add these depends to the sections dependents
    sobj.Depends = depends_list

    # for backwards compatibility we need to call the "old" mapper logic for resolving values
    # ideally going forward this code is only called when we have builders that add exportable item
    # as part of the build process. At the moment there are clear cases for this.. but it should not be common
    # unless this DependsOn() and we set a value to say assume that we are using a new format, we have to
    # assume that something might depend on the older logic.

    # update this later
    #if sobj.isClassicFormat: # change this function so we can assume it false at some point
    # do classic mapper connections to get data where we needed it
    depends_on_classic(env, depends_list)

def resolve_depends(sobj):

    # get depends
    depends = sobj.Depends





class dependsOnEnv:

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, depends):
        return self.env.DependsOn(depends)


# adding logic to Scons Environment object
SConsEnvironment.DependsOn = depends_on
SConsEnvironment.Component = Component
# allow us to add component to parts as a global objects
api.register.add_global_parts_object('DependsOn', dependsOnEnv, True)
api.register.add_global_parts_object('Component', ComponentEnv, True)
api.register.add_global_parts_object('REQ', requirement.REQ)
