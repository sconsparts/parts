

import json

import parts.api as api
import parts.core.scanners as scanners
import parts.glb as glb
import parts.pnode.dependent_info as dependent_info
import SCons.Script
from SCons.Script.SConscript import SConsEnvironment

from .. import util

file_name = "${PARTS_SYS_DIR}/${PART_ALIAS}.${PART_SECTION}.exports.jsn"


def PartExportsAction(target, source, env):

    section = glb.engine._part_manager._from_env(env).Section(env["PART_SECTION"])

    data = {}
    # create data structure for the exported data
    for k, v in section.Exports.items():
        v = env.Flatten(v)
        if v != []:
            data[k] = v
    # write out the data
    with open(target[0].get_path(), 'w') as outfile:
        data = json.dumps(
            data,
            indent=2,
            cls=util.SetNodeEncode
        )
        outfile.write(data)


def map_export(env, source):

    section = glb.engine._part_manager.section_from_env(env)

    targets = section.Env._part_exports_(
        # the output should be resolve based on the environment of the section
        section.Env.File(file_name),

        # I believe we want this to depend on other .jsn files we generated
        # some of the jsn file might be sync points for dynamic builders
        # only these dynamic builder will generate files that are not part
        # of the data state parts is generating. the default static builders
        # don't get mapped to this jsn based state files.
        source,
    )
    return targets


def source_scanner(node, env, path):
    # this just prevents SCons from calling default scanner on node such as directories
    api.output.verbose_msgf(["export-scanner", "scanner", "scanner-called"], "Scanning node {0}", node.ID)
    return []


api.register.add_builder('_part_exports_', SCons.Builder.Builder(
    name="export-state",
    action=SCons.Action.Action(PartExportsAction, "Writting exported values in $TARGET"),
    target_factory=SCons.Node.FS.File,
    source_factory=SCons.Node.FS.Entry,
    source_scanner=SCons.Script.Scanner(source_scanner, name="export-scan"),
    target_scanner=scanners.NullScanner,
    multi=1
))

SConsEnvironment._map_export_ = map_export
