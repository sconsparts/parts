
import glb
import part_ref
import dependent_ref
import version
import common
import core.util as util
import functors
import api
import errors
import target_type
import api.requirement

from requirement import REQ

import SCons.Script

from SCons.Debug import logInstanceCreation


def Component(env, name, version_range=None, requires=REQ.DEFAULT, section="build"):

    # fix up the name string
    if name.startswith("name::") == False:
        name = 'name::{0}'.format(name)
    # make it a target
    t = target_type.target_type(name)
    # get pobj
    pobj = glb.engine._part_manager._from_env(env)
    # get any local space that was set
    localspace = pobj.Uses
    # try to auto select version
    # this way we don't have to say env.PartVersion() when depending on
    # subparts that are in the same Root Part
    if version_range is None:
        if pobj.Root.Name == name.split('.')[0]:
            version_range = pobj.Version
    else:
        version_range = version.version_range(version_range)
    # set the version value
    if version_range:
        t.Properties['version'] = version_range
    elif t.Properties.has_key('version') == False:
        t.Properties['version'] = '*'
    # set the target value
    if t.Properties.has_key('target') == False:  # ['target','target-platform','target_platform']
        t.Properties['platform_match'] = env['TARGET_PLATFORM']

    # Set the configuration to try to match
    if t.Properties.has_key('config') == False:
        t.Properties['config'] = str(env['CONFIG'])

    return dependent_ref.dependent_ref(part_ref.part_ref(t, localspace), section, requires)


class ComponentEnv(object):

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, name, version_range=None, requires=REQ.DEFAULT):
        return self.env.Component(name, version_range, requires)


def depends_on_classic(env, depends):
    '''
    This form requires that all dependance get defined by a "mapper" object.
    This allow for delay processing that is required as at any given time this
    is call we don't really know all the Parts object that could exist. So we leave
    a "calling" card for what we want to find in this place.
    '''
    errors.SetPartStackFrameInfo()
    pobj = glb.engine._part_manager._from_env(env)
    if pobj is None:
        return

    # check to see if we need to some funky preloads as we map the dependancy values
    # this is needed to help case of Parts files changes that might have added
    # new dependancy values. We let the loader deal with the issues.
    # the dependancy mapping logic for the classic case stays unchanged
    glb.engine._part_manager.Loader.process_depends(pobj, depends)

    api.output.verbose_msg('dependson', "Mapping data to Part", pobj.Name)
    # depends that get passed on
    if util.isList(depends) == False:
        depends = [depends]

    for comp in depends:
        # quick error check
        if pobj.Name == comp.PartRef.Target.Name and pobj.DefiningSection.Name == comp.SectionName:
            api.output.warning_msg("Part depends on with itself")
            api.output.print_msg("Skipping the definition of dependence to SCons")
            continue
        api.output.verbose_msg('dependson', " Component", comp.PartRef.Target.Name)
        glb.engine.add_preprocess_logic_queue(
            functors.map_depends(pobj.DefiningSection.Env, comp.PartRef, comp.SectionName, comp.Requires, comp.StackFrame)
        )
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
            map_val = r.value_mapper(comp.PartRef.Target, comp.SectionName)
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
                if env.has_key(r.key):
                    env[r.key] = [env[r.key], map_val]
                else:
                    env[r.key] = map_val
            # export logic
            # if this is not internal we add to the current component export table
            if r.is_internal == False:
                api.output.verbose_msg('dependson', "  exporting", r.key, map_val)
                if r.key not in pobj.DefiningSection.Exports and r.is_list:
                    pobj.DefiningSection.Exports[r.key] = [[]]

                if r.is_list:
                    pobj.DefiningSection.Exports[r.key] = common.extend_unique(pobj.DefiningSection.Exports[r.key], [[map_val]])
                else:
                    pobj.DefiningSection.Exports[r.key] = map_val
                api.output.verbose_msg('dependson', "  Exported values", pobj.DefiningSection.Exports[r.key])

    # map up rpath with this.. ( need to fix up the Mac)
    if env['TARGET_PLATFORM'] != 'win32' and env['TARGET_PLATFORM'] != 'darwin':
        def_env = glb.engine
        glb.engine.add_preprocess_logic_queue(functors.map_rpath_part(env))
        glb.engine.add_preprocess_logic_queue(functors.map_rpath_link_part(env, pobj.DefiningSection))

    errors.ResetPartStackFrameInfo()


def depends_on(env, depends):

    pobj = glb.engine._part_manager._from_env(env)
    if pobj is None:
        print "fill me in"
        return

    depends_list = []
    # make this a list if it is not already
    if util.isList(depends) == False:
        depends = [depends]

    # make any string a component object
    for i in depends:
        if util.isString(i):
            depends_list.append(Component(env, i))
        else:
            depends_list.append(i)

    # set the target platform in case we want to acces the part object this
    # would produce latter
    # for i in depends_list:
        # i.target=env['TARGET_PLATFORM']
        # i.local_space=pobj.Uses

    # set what we depend on
    # this will be resolved latter when we process the Parts objects

    pobj.DefiningSection.Depends = depends_list

    # if this is classic case we will want to resolve now.
    if pobj.isClassicFormat:
        # do classic mapper connections to get data where we needed it
        depends_on_classic(env, depends_list)


class dependsOnEnv(object):

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, depends):
        return self.env.DependsOn(depends)


# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.DependsOn = depends_on
SConsEnvironment.Component = Component
# allow us to add component to parts as a global objects
api.register.add_global_parts_object('DependsOn', dependsOnEnv, True)
api.register.add_global_parts_object('Component', ComponentEnv, True)
api.register.add_global_parts_object('REQ', REQ)
