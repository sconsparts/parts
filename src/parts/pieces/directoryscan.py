
from __future__ import absolute_import, division, print_function

import hashlib
import os
import json

import parts.api as api
import parts.common as common
import parts.core.builders as _builders
import parts.node_helpers as node_helpers
import parts.core.util as util
import SCons.Script
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# might want to move this function to a generic dummy file action
def WriteScanResultState(target, source, env):
    # generate the state file name
    md5 = hashlib.md5()
    md5.update(target[0].ID.encode())
    name_hash = md5.hexdigest()
    state_file = env.File("${{PARTS_SYS_DIR}}/${{PART_ALIAS}}.${{PART_SECTION}}.dyn.scan.{}.jsn".format(name_hash))
    # scan the directory for files. These are all outputs of building the directory
    snode = env.Pattern(src_dir=target[0]).files()
    # write out these file to disk, so we can use it later as state
    # for SideEffects of build this directory when nothing change to build
    # the directory
    with open(state_file.get_path(), 'w') as outfile:
        json.dump(snode, outfile, cls=util.SetNodeEncode)


WriteScanResultStateAction = SCons.Action.Action(
                WriteScanResultState,
                "Scanning '$TARGET' for files"
            )


def DynScanPath(env, node, target, source, args):    
    ##################################################################
    # get the sources and add a import.dyn.jsn as a depends
    # this insures that values that are defined by dependents that are
    # being dynamic as well go off correctly so we can make our up-to-date
    # check correct run those scanners
    for s in source:
        # todo?? 
        # double check if we are a depends already!!!!
        env.Depends(s,env.File(_builders.dyn_imports.file_name))
    return ()

cache = {}

def _DynamicDirScanner(node, env, path, args):
    api.output.verbose_msgf(["scandirectory-scanner", "scanner", "scanner-called"], "Scanning node {0}", node.ID)
    ##################################################################
    # get data on what we might need to process
    use_scan_defaults = args.get("use_scan_defaults", env.get("use_scan_defaults", True))
    scan_callbacks = args.get("scan_callbacks", env.get("scan_callbacks", []))
    scan_overrides = args.get("scan_overrides", env.get("scan_overrides", {}))
    default_mappings_dict = args.get("default_mappings_dict", env.get("default_mappings_dict", {}))
    extra_scanner = args.get("extra_scanner")    
    results = []

    ########################################################################
    # set post action
    # have to do it in scanner since the generation of the scanner does 
    # not have a builder defined yet
    api.output.verbose_msgf(["scandirectory-scanner", "scanner"], "Checking post action")
    executor = node.get_executor()
    # check that this action is not defined already in the post actions, else add it 
    # this is needed because adding it twice will cause false rebuilds that we want to avoid
    if WriteScanResultStateAction not in executor.post_actions:
        api.output.verbose_msgf(["scandirectory-scanner", "scanner"], "Adding post action")
        env.AddPostAction(
            node,
            WriteScanResultStateAction
        )

    # did the node have explict changes
    changed = node_helpers.has_changed(node,skip_implict=True)
    if not changed and node.ID in cache:        
        api.output.verbose_msgf(["scandirectory-scanner", "scanner"], "Returning cache {0}", node.ID)
        # if we are up-to-date or are built and we are in the cache
        # return this to save time and avoid duplicates
        return cache[node.ID]
    else:
        # call the extra scanner if needed
        # common case might be calling a ProgScan for building third party build system
        # so we can make sure libs it would need are ready to go        
        scan_results=[]
        if extra_scanner:
            api.output.verbose_msgf(["scandirectory-scanner", "scanner"], "Calling extra scanner {0}", node.ID)
            scan_results=extra_scanner(
                node,
                env,
                extra_scanner.path(
                    env,
                    None,
                    executor.get_all_targets(),
                    executor.get_all_sources()
                )
            )

    if changed:
        # if we are not up to date and we are not built
        # stop main directory scan as it will may be incorrect
        api.output.verbose_msgf(["scandirectory-scanner", "scanner"], "Change detected, skipping scan")
        return scan_results
    else:
        api.output.verbose_msgf(["scandirectory-scanner", "scanner"], "Full scan {0}", node.ID)
        # do the full directory scans as the directory is now built
        # We can "trust" the state on disk should be good at this point
        node = env.arg2nodes(node, env.fs.Dir)[0]

        if node.isBuilt or node.isVisited:
            # we can scan the disk to get the information
            # as this state is correct and up to date
            snode = env.Pattern(src_dir=node).files()            
            env.SideEffect(snode, node)

        # default logic we want to look for
        default_mappings = env.get("SCANDIR_DEFAULTS", default_mappings_dict if use_scan_defaults else {})

        # merging in custom logic
        overides = env.get("SCANDIR_OVERRIDES", scan_overrides)

        for key, value in overides.items():
            if isinstance(value, dict):
                default_mappings[key].update(value)
            else:
                default_mappings[key] = value

        # go over the items in the final set
        for builder, inputs in default_mappings.items():

            # test that we have the builder/function
            if not hasattr(env, builder):
                api.output.error_msg("Environment does not have member '{}'".format(builder))
            func = getattr(env, builder)
            # process the arguments
            # is this a function? call it
            if not inputs:
                api.output.verbose_msg(["scandirectory-scanner", "scanner"], "{} is none, skipping!".format(builder))
                continue
            elif callable(inputs):
                args = inputs(node, env)
            elif isinstance(inputs, dict):
                args = {}
                for arg, value in inputs.items():
                    if callable(value):
                        args[arg] = value(node, env)
                    else:
                        args[arg] = value
            else:
                api.output.error_msg(
                    "{1} must be a dictionary of arguments or a callable\n Type provided was {2}".format(key, type(inputs)))

            # call the function
            api.output.verbose_msg(["scandirectory-scanner", "scanner"], "calling builder {0}".format(builder), args)
            out = func(allow_duplicates=True, _PARTS_DYN=True, **args)
            api.output.verbose_msg(["scandirectory-scanner", "scanner"], "Adding nodes {0}".format([str(o) for o in out]))
            results += out

        callbacks = env.get("SCANDIR_CALLBACKS", scan_callbacks)
        v1=env.get('allow_duplicates')
        v2=env.get('_PARTS_DYN')
        env['allow_duplicates']=True
        env['_PARTS_DYN']=True        
        for callback in callbacks:
            callback(node, env)
        env['allow_duplicates']=v1
        env['_PARTS_DYN']=v2
        api.output.verbose_msgf(["scandirectory-scanner", "scanner", "scanner-results"],
                                "Scanning results {0}", [str(r) for r in results])

        cache[node.ID] = scan_results

    return scan_results


def ScanDirectory(env, default_dir, defaults=True, callbacks=[], extra_scanner=None, **builders):
    ''' 
    This returns a scanner to the scan a directory. It also calls a builder to a dyn.jsn file
    to help allow control flow of imported variable and depends handling in the taskmaster
    '''

    default_dir = env.arg2nodes(default_dir, env.Dir)
    use_scan_defaults = defaults
    scan_callbacks = common.make_list(callbacks)
    scan_overrides = builders
    default_mappings_dict = dict(
        InstallBin=dict(
            source=lambda node, env, default=None: [
                env.Pattern(src_dir=node.Dir("bin"), includes=env["INSTALL_BIN_PATTERN"]),
                env.Pattern(src_dir=node.Dir("bin32"), includes=env["INSTALL_BIN_PATTERN"]),
                env.Pattern(src_dir=node.Dir("bin64"), includes=env["INSTALL_BIN_PATTERN"]),
            ]
        ),
        InstallLib=dict(
            source=lambda node, env, default=None: [
                env.Pattern(src_dir=node.Dir("lib"), includes=env["INSTALL_LIB_PATTERN"] + env["INSTALL_API_LIB_PATTERN"]),
                env.Pattern(src_dir=node.Dir("lib32"), includes=env["INSTALL_LIB_PATTERN"] + env["INSTALL_API_LIB_PATTERN"]),
                env.Pattern(src_dir=node.Dir("lib64"), includes=env["INSTALL_LIB_PATTERN"] + env["INSTALL_API_LIB_PATTERN"]),
            ],
        ),
        InstallPkgConfig=dict(
            source=lambda node, env, default=None: [
                env.Pattern(src_dir=node.Dir("lib/pkgconfig"), includes=["*.pc"]),
                env.Pattern(src_dir=node.Dir("lib32/pkgconfig"), includes=["*.pc"]),
                env.Pattern(src_dir=node.Dir("lib64/pkgconfig"), includes=["*.pc"]),
            ],
        ),
        InstallInclude=dict(
            source=lambda node, env, default=None: [
                env.Pattern(src_dir=node.Dir("include"), includes=["*.h", "*.H", "*.hxx", "*.hpp", "*.hh"]),
                env.Pattern(src_dir=node.Dir("include32"), includes=["*.h", "*.H", "*.hxx", "*.hpp", "*.hh"]),
                env.Pattern(src_dir=node.Dir("include64"), includes=["*.h", "*.H", "*.hxx", "*.hpp", "*.hh"]),
            ],
        ),

        InstallConfig=dict(
            source=lambda node, env, default=None: [
                env.Pattern(src_dir=node.Dir("etc"), includes=["*"]),
            ],
        ),

        InstallLibExec=dict(
            source=lambda node, env, default=None: [
                env.Pattern(src_dir=node.Dir("libexec"), includes=["*"]),
            ],
        ),
    )

    # this generates the name of the side effect jsn file that stores state about what this scanned
    # having this data may not prove useful beyond debugging. however the file defines a known
    # pathway for everythign to scan correctly on incremental builds. This is done via having 
    # a set of state files that map imported and exported builder between components. This allows
    # the task logic to find and call the scanner to define nodes and or environment values to allow
    # the scanners and builder to work correctly when values are subst()
    md5 = hashlib.md5()
    md5.update(default_dir[0].ID.encode())
    name_hash = md5.hexdigest()
    state_file_name = env.File("${{PARTS_SYS_DIR}}/${{PART_ALIAS}}.${{PART_SECTION}}.dyn.scan.{}.jsn".format(name_hash))
    state_file_name.Decider("timestamp-match")
    env.SideEffect(state_file_name, default_dir)
    env.Clean(default_dir,default_dir)
    # because we know this is dynamic we need to define 
    # that the dyn.import.jsn need to be generated for this file
    #env._map_dyn_imports_()
    # map this file to the dyn.exports.jsn file
    env._map_dyn_export_(state_file_name)

    extras = dict(
        use_scan_defaults=use_scan_defaults,
        scan_callbacks=scan_callbacks,
        scan_overrides=scan_overrides,
        default_mappings_dict=default_mappings_dict,
        extra_scanner=extra_scanner,
        scan_return_source=True,
    )

    return SCons.Script.Scanner(
        _DynamicDirScanner, 
        path_function=DynScanPath,
        argument=extras      
        )

SConsEnvironment.ScanDirectory = ScanDirectory
