

import json

import parts.api as api
import parts.common as common
import parts.pnode as pnode
import parts.core.scanners as scanners
import parts.glb as glb
#import parts.pnode.dependent_info as dependent_info
import SCons.Script
from SCons.Script.SConscript import SConsEnvironment

from .. import util

file_name = "${PARTS_SYS_DIR}/${PART_ALIAS}.${PART_SECTION}.exports.jsn"


def SectionStateAction(target, source, env):
    '''
    We are writing out the state of the section to a file. This is used to help
    check for various items to help speed up the build by allowing for information
    for various checks, or to help clean up outputs that need to re generated.
    '''

    
    

    section:pnode.section.Section = glb.engine._part_manager._from_env(env).Section(env["PART_SECTION"])

    data = {}
    # get the dependent sections we depend on 
    dependent_sections = section.Depends
    
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
    target = section.Env.File(file_name)
    targets = [target]
    source = common.make_list(source)
    if (source and not all(src in target.sources for src in source)) or not target.has_builder():
        # if source or not target.has_builder():

        targets = section.Env._part_exports_(
            # the output should be resolve based on the environment of the section
            targets,

            # I believe we want this to depend on other .jsn files we generated
            # some of the jsn file might be sync points for dynamic builders
            # only these dynamic builder will generate files that are not part
            # of the data state parts is generating. the default static builders
            # don't get mapped to this jsn based state files.
            source,
        )
        # for the scanner to make sure we go down and scan items with dynamic states correctly
        targets[0].attributes._is_dyn_generated = True
        api.output.verbose_msg(["builder.export.static", "builder.export", "builder"],
                               f"Mapping export file {targets[0]} -> {source}")
    else:
        api.output.verbose_msg(["builder.export.static", "builder.export", "builder"],
                               f"Skipped builder call {targets[0]}, source={source}, target={target.sources}")
    return targets


def source_scanner(node, env, path):
    # this just prevents SCons from calling default scanner on node such as directories

    section = glb.engine._part_manager._from_env(env).Section(env["PART_SECTION"])
    api.output.verbose_msgf(["scanner.export.static", "scanner.export", "scanner", "scanner.called"],
                            f"Scanning node {node.ID} Section={section.ID}")

    if hasattr(node.attributes, "_is_dyn_generated"):
        api.output.verbose_msgf(["scanner.export.static", "scanner.export", "scanner", ],
                                f"{node.ID} needs to be dynamically scanned")
        node.scan()
        api.output.verbose_msgf(["scanner.export.static", "scanner.export", "scanner", ], f"{node.ID} scan done")
    return []


def target_scanner(node, env, path):
    section = glb.engine._part_manager._from_env(env).Section(env["PART_SECTION"])
    api.output.verbose_msgf(["scanner.export.static", "scanner.export", "scanner", "scanner.called"],
                            f"Scanning node {node.ID} Section={section.ID}")
    nodes = set()
    # create data structure for the exported data
    for k, v in section.Exports.items():
        if k.startswith("SDK") and k != "SDK":
            # add the SDKXXX node.. we SKIP SDK as that is different
            v = env.Flatten(v)
            if v != []:
                # print(f"scan->{v}")
                nodes.update(v)
    ret = list(nodes)
    ret.sort()
    #print(f"-scan {node.ID}\n ret={ret}")
    api.output.verbose_msgf(["scanner.export.static", "scanner.export", "scanner", ],
                            f" Section={section.ID} {node.ID} ret count={len(ret)}")
    return ret


api.register.add_builder('_section_state_', SCons.Builder.Builder(
    name="section-state",
    action=SCons.Action.Action(PartExportsAction, "Writing state values in $TARGET"),
    target_factory=SCons.Node.FS.File,
    source_factory=SCons.Node.FS.Entry,
    # source_scanner=scanners.NullScanner,
    source_scanner=SCons.Script.Scanner(source_scanner, name="section-scan"),  # scanners.NullScanner,
    # target_scanner=scanners.NullScanner,
    target_scanner=SCons.Script.Scanner(target_scanner, name="section-scan"),  # scanners.NullScanner,
    multi=1
))

api.register.add_method(map_export, '_map_export_')
