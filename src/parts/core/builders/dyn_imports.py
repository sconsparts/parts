

import json

import parts.api as api
import parts.glb as glb
import parts.pnode.dependent_info as dependent_info
from .. import util
import SCons.Script
from SCons.Script.SConscript import SConsEnvironment


def PartDynImportsAction(target, source, env):
    data = {}
    # get the part object
    pobj = glb.engine._part_manager._from_env(env)
    # get the section
    sec = pobj.Section(env["PART_SECTION"])

    # generate the data
    for comp in sec.Depends:
        if not comp.hasUniqueMatch and comp.isOptional:
            continue
        for r in comp.Requires:
            map_val = r.value_mapper(comp.PartRef.Target, comp.SectionName, comp.isOptional)
            value = env.subst(map_val)
            if r.key in data:
                if value and value not in data[r.key]:
                    data[r.key].append(value)
            elif value:
                data[r.key] = [value]

    # store information about we will import
    with open(target[0].get_path(), 'w') as outfile:

        data = json.dumps(
            data,
            indent=2,
            cls=util.SetNodeEncode
        )
        outfile.write(data)


def depend_dyn_scanner(node, env, path):
    from . import dyn_exports
    # depends scanner will resolve the depends of the part
    # and map a then map the export.jsn file for the part
    api.output.verbose_msgf(["import-dyn-scanner", "scanner", "scanner-called"], "Scanning node {0}", node.ID)
    # get the part object
    pobj = glb.engine._part_manager._from_env(env)
    # get the section
    sec = pobj.Section(env["PART_SECTION"])
    ret = []
    for comp in sec.Depends:
        if not comp.hasUniqueMatch and comp.isOptional:
            continue
        if comp.Section.hasDynamicExports:
            tmp = comp.Section.Env.File(dyn_exports.file_name)
            api.output.verbose_msgf(["import-dyn-scanner", "scanner"], " Adding node {0}", tmp.ID)
            ret.append(tmp)

    return ret


file_name = "$PARTS_SYS_DIR/${PART_ALIAS}.${PART_SECTION}.dyn.imports.jsn"


def map_dyn_imports(env, section=None):
    if not section:
        section = glb.engine._part_manager._from_env(env).Section(env["PART_SECTION"])

    targets = []
    # generate a dynamic import if we have depends and if we have a depends that has dynamic_export
    if section.Depends and section.hasDynamicExports:
        targets = env._part_dyn_imports_(
            # the output should be resolve based on the environment of the section
            section.Env.subst(file_name),
            # sources are a value that holds a mostly readable hash of the depends
            [],
            section=section,
        )

    return targets


api.register.add_builder('_part_dyn_imports_', SCons.Builder.Builder(
    name="dynamic-import-state",
    action=SCons.Action.Action(PartDynImportsAction, "Writting dynamically imported values in $TARGET"),
    target_factory=SCons.Node.FS.File,
    source_factory=SCons.Node.Python.Value,
    target_scanner=SCons.Script.Scanner(depend_dyn_scanner, name="dyn-import-scan"),
))

SConsEnvironment._map_dyn_imports_ = map_dyn_imports
