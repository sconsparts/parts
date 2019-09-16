from __future__ import absolute_import, division, print_function
import json

import parts.api as api
import parts.glb as glb
import parts.common as common
import parts.packaging as packaging
import parts.core.util as util
import parts.node_helpers as node_helpers
import parts.core.builders as builders
import SCons.Script
from SCons.Script.SConscript import SConsEnvironment
##################################
# defines two builders
#
# one builder is the builder that generated a json file
# that contains all the installed files sort package group
# This is used as sync point in the depends tree for dynamic
# builders that would install items.
#
# the second builder is generates a json file for a given package group
#
# ideal in both cases I think this could be done with Value node
# given they are fixed a little. This would be better as the information
# would be in memory and I would not need to create a set of files

global_file_name = "$PARTS_SYS_DIR/package.groups.jsn"

# the wrapper function
def DynamicPackageNodes(_env, source):
    '''
    This file defines all the files that will be packagable for any given group
    It is in the depend chain for creating any package that we need to generate
    '''
    # make sure we have a common environment for this mutli build
    # is it needs to be defined at a "global" level
    env = glb.engine.def_env
    # this defines the 
    targets = env._DynamicPackageNodes(global_file_name, source)
    [t.Decider("timestamp-match") for t in targets]
    return targets
    

def WritePackageGroupFiles(target, source, env):
    # This write out all the files that would be install
    # orginized by the groups
    with open(target[0].get_path(), 'w') as outfile:        
        data = json.dumps(
            dict(
                pkg=packaging._sorted_groups[0],
                no_pkg=packaging._sorted_groups[1]
            ),
            indent=2,
            cls=util.SetNodeEncode
        )
        outfile.write(data)

def target_scanner(node, env, path):
    # clear any cached data as regen file list
    # should only need to be called here as after this target is called we should have
    # called all "installXXX" functions that would define a node to install
    if not node_helpers.has_changed(node,skip_implict=True):
        api.output.verbose_msg(["dynamicpackage-scanner", "scanner", "scanner-called"], "called {}".format(node.ID))
        packaging.SortPackageGroups()
        packaging._sorted_groups
    return []


# this allow us to define a "dynamic" value that will have to be build
# before we try to get nodes for a given group. This is call via a wrapper
# to ensure a common environment
api.register.add_builder('_DynamicPackageNodes', SCons.Builder.Builder(
    action=SCons.Action.Action(WritePackageGroupFiles, "Sync any dynamic builder with node that are packaged"),
    target_factory=SCons.Node.FS.File,
    source_factory=SCons.Node.FS.File,
    target_scanner=SCons.Script.Scanner(target_scanner),
    multi=1
))

###########################################################################
###########################################################################

# the wrapper function
def GroupBuilder(env, source, no_pkg=False, **kw):
    '''
    This builder will make a json file and set some node values for 
    a given package group. It will depend on the "master" dynamic.package.jsn
    file that will contain a all the package files and group that are defined
    '''


    # make sure we have a common environment for this mutli build
    out = env._GroupBuilder(
        target=source,
        source=[],     
        allow_duplicates=True,
        **kw
    )
    return out


def GroupBuilderAction(target, source, env):
    new_sources, no_pkg = env.GetFilesFromPackageGroups("target", [target[0].name.split(".")[2]])
    if not env.get("no_pkg", False):
        target[0].attributes.GroupFiles = new_sources
    else:
        target[0].attributes.GroupFiles = no_pkg

    with open(target[0].get_path(), 'w') as outfile:
        data = json.dumps([i.ID for i in target[0].attributes.GroupFiles], indent=2,)
        outfile.write(data)

def emit(target, source, env):
    # need to be absolute on the path as the VariantDir() is a global value
    # that effect everything, it is not per environment
    ret = []
    for trg in target:
        trg = env.File("${{PARTS_SYS_DIR}}/package.group.{}.jsn".format(trg.ID))
        trg.Decider("timestamp-match")        
        ret.append(trg)
    return ret, source


def GroupNodesScanner(node, env, path):
    
    api.output.verbose_msg(["groupbuilder-scanner", "scanner", "scanner-called"], "called {}".format(node.ID))
    # this is the default group we depend on unless the node has a meta value saying that this 
    # can be defined on the export.jsn file of this part instead

    local = env.MetaTagValue(node, 'local_group', 'parts',False)
    if local:
        ret = [env.File(builders.exports.file_name)]
    else:
        ret = [env.File(global_file_name)]

    # make sure the groups are sorted
    if not node_helpers.has_changed(node, skip_implict=True):
        node = node.name.split(".")[2]
        new_sources, _ = env.GetFilesFromPackageGroups("", [node])
        #ret += new_sources
    
    api.output.verbose_msgf(["groupbuilder-scanner", "scanner"],"Returned {}",common.DelayVariable(lambda :[i.ID for i in ret]))
    return ret


api.register.add_builder('_GroupBuilder', SCons.Builder.Builder(
    action=SCons.Action.Action(GroupBuilderAction, "looking up files in package group '${TARGET.name.split(\'.\')[2]}'"),
    target_factory=SCons.Node.FS.File,
    source_factory=SCons.Node.Python.Value,
    emitter=emit,
    target_scanner=SCons.Script.Scanner(GroupNodesScanner),
    multi=True
))

SConsEnvironment.GroupBuilder = GroupBuilder
SConsEnvironment.DynamicPackageNodes = DynamicPackageNodes
