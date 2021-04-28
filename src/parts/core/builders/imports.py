

import json

import parts.api as api
import parts.glb as glb
import parts.pnode.dependent_info as dependent_info
from .. import util
from . import exports
import SCons.Script


def PartImportsAction(target, source, env):
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


def depend_scanner(node, env, path):
    # depends scanner will resolve the depends of the part
    # and map a then map the export.jsn file for the part
    api.output.verbose_msgf(["import-scanner", "scanner", "scanner-called"], "Scanning node {0}", node.ID)
    # get the section
    sec = glb.engine._part_manager.section_from_env(env)
    ret = []
    for comp in sec.Depends:
        if not comp.hasUniqueMatch and comp.isOptional:
            # nothing was found and this was an optional depends
            # so we can skip this
            continue
        # add the expected depend on the export file
        export_file = comp.Section.Env.File(exports.file_name)
        api.output.verbose_msg(["import-scanner", "scanner"],f"  mapping {export_file.ID}")
        ret.append(comp.Section.Env.File(export_file))
        # map the higher level aliases
        for requirement in comp.Requires:
            value = comp.Section.Exports.get(requirement.key)
            if value and requirement.mapto:
                targets = requirement.mapto(sec)
                for t in targets:
                    sec._map_target(value, t)

    return ret


file_name = "$PARTS_SYS_DIR/${PART_ALIAS}.${PART_SECTION}.imports.jsn"


def map_imports(env, section):
    targets = []
    if section.Depends:
        targets = env._part_imports_(
            # the output should be resolve based on the environment of the section
            section.Env.subst(file_name),
            # sources are a value that holds a mostly readable hash of the depends
            [],  # [env.Value(d.str_sig()) for d in section.Depends],
            section=section,
        )
    return targets


api.register.add_builder('_part_imports_', SCons.Builder.Builder(
    name="import-state",
    action=SCons.Action.Action(PartImportsAction, "Writting dynamically imported values in $TARGET"),
    target_factory=SCons.Node.FS.File,
    source_factory=SCons.Node.Python.Value,
    target_scanner=SCons.Script.Scanner(depend_scanner, name="import-scan"),
))
