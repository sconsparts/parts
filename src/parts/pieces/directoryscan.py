

import hashlib
import os
import json
from pickle import FALSE

import parts.glb as glb
import parts.api as api
import parts.common as common
import parts.core.builders as _builders
import parts.node_helpers as node_helpers
import parts.core.util as util
from parts.core.states import ChangeCheck
import SCons.Script

# might want to move this function to a generic dummy file action


def WriteScanResultState(target, source, env):
    # generate the state file name
    md5 = hashlib.md5()
    md5.update(target[0].ID.encode())
    name_hash = md5.hexdigest()
    state_file = env.File(
        "${{PARTS_SYS_DIR}}/${{PART_ALIAS}}.${{PART_SECTION}}.dyn.scan.{}.jsn".format(name_hash))
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


# def DynScanPath(env, node, target, source, args):
#     ##################################################################
#     # get the sources and add a import.dyn.jsn as a depends
#     # this insures that values that are defined by dependents that are
#     # being dynamic as well go off correctly so we can make our up-to-date
#     # check correct run those scanners
#     api.output.verbose_msgf(["scanner.dynscanpath", "scanner", "scanner.called"], "Scanning node {0}", node.ID)
#     section = glb.engine._part_manager.section_from_env(env)
#     # if not section.DefiningPhase or section.Depends:
#     if section.Depends:
#         dyn_import_file = env.File(_builders.dyn_imports.file_name)
#         for s in source:
#             # only add if the node is a target as adding to a node that has no builder
#             # has no effect and makes a ugly tree
#             if s.has_builder():
#                 print(f"99   {s} -> {dyn_import_file}")
#                 env.Depends(s, dyn_import_file)
#     return ()


cache = {}


def _DynamicDirScanner(node, env, path, args):
    api.output.verbose_msgf(["scanner.scandirectory", "scanner",
                            "scanner.scandirectory.called", "scanner.called"], "Scanning node {0}", node.ID)
    ##################################################################
    # get data on what we might need to process

    use_scan_defaults = args.get(
        "use_scan_defaults", env.get("use_scan_defaults", True))
    scan_callbacks = args.get("scan_callbacks", env.get("scan_callbacks", []))
    scan_overrides = args.get("scan_overrides", env.get("scan_overrides", {}))
    default_mappings_dict = args.get(
        "default_mappings_dict", env.get("default_mappings_dict", {}))
    extra_scanner = args.get("extra_scanner")
    results = []
    env['_DYNSCANNER_NODE'] = node
    ########################################################################
    # set post action
    # have to do it in scanner since the generation of the scanner does
    # not have the correct builder defined when we generate the scanner.
    api.output.verbose_msgf(
        ["scanner.scandirectory", "scanner"], "Checking post action")
    executor = node.get_executor()
    # check that this action is not defined already in the post actions, else add it
    # this is needed because adding it twice will cause false rebuilds that we want to avoid
    if WriteScanResultStateAction not in executor.post_actions:
        api.output.verbose_msgf(
            ["scanner.scandirectory", "scanner"], "Adding post action")
        env.AddPostAction(
            node,
            WriteScanResultStateAction
        )

    # did the node have explicit changes
    #changed = node_helpers.has_changed(node, skip_implicit=False) & ChangeCheck.DIFF
    if node.ID in cache:
        api.output.verbose_msgf(["scanner.scandirectory", "scanner",
                                "scanner.scandirectory.cached"], "Returning cache {0}", node.ID)
        # if we are up-to-date or are built and we are in the cache
        # return this to save time and avoid duplicates
        return cache[node.ID]
    else:

        # call the extra scanner if needed
        # common case might be calling a ProgScan for building third party build system
        # so we can make sure libs it would need are ready to go
        scan_results = []
        if extra_scanner:
            scan_results = extra_scanner(
                node,
                env,
                extra_scanner.path(
                    env,
                    None,
                    executor.get_all_targets(),
                    executor.get_all_sources()
                )
            )
            api.output.verbose_msgf(["scanner.scandirectory", "scanner"],
                                    f"Calling extra scanner {node.ID}: results: {scan_results}")
    # did the node have explicit changes
    # we cannot include implict changes yet as this scanner would be returning these values
    # for this node, so binfo checks would see a difference of missing nodes.
    #print(f"calling 3 {node}")
    changed = node_helpers.has_changed(
        node, skip_implicit=True) & ChangeCheck.DIFF
    if changed:
        # if we are not up to date and we are not built
        # stop main directory scan as it will may be incorrect
        api.output.verbose_msgf(["scanner.scandirectory", "scanner",
                                "scanner.scandirectory.skip"], "Change detected, skipping scan")
        return scan_results
    else:
        api.output.verbose_msgf(
            ["scanner.scandirectory", "scanner"], "Full scan {0}", node.ID)
        # do the full directory scans as the directory is now built
        # We can "trust" the state on disk should be good at this point
        node = env.arg2nodes(node, env.fs.Dir)[0]

        if node.isBuilt or node.isVisited:
            # we can scan the disk to get the information
            # as this state is correct and up to date
            snode = env.Pattern(src_dir=node).files()
            env.SideEffect(snode, node)

        # merging in custom logic
        overides = env.get("SCANDIR_OVERRIDES", scan_overrides)

        # default logic we want to look for
        # we either have a special user based mapping Via the SCANDIR_DEFAULTS value or we
        # use the default_mapping that was passed in via default_mappings_dict.
        # the value of use_scan_defaults will control if we use the defined defaults or user based ones
        if use_scan_defaults:
            default_mappings = default_mappings_dict
        else:
            default_mappings = env.get("SCANDIR_DEFAULTS", {})
            if not default_mappings and not overides and not scan_callbacks:
                api.output.warning_msg(
                    "SCANDIR_DEFAULTS is an empty dictionary.")

        for key, value in overides.items():
            # make copy of item to override
            default_mappings[key] = default_mappings.get(key, {}).copy()
            # do the override
            if isinstance(value, dict) and key in default_mappings:
                default_mappings[key].update(value)
            else:
                default_mappings[key] = value
        # go over the items in the final set
        v1 = env.get('allow_duplicates')
        v2 = env.get('_PARTS_DYN')
        env['allow_duplicates'] = True
        env['_PARTS_DYN'] = True
        for builder, inputs in default_mappings.items():

            # test that we have the builder/function
            if not hasattr(env, builder):
                api.output.error_msg(
                    "Environment does not have member '{}'".format(builder))
            func = getattr(env, builder)
            # process the arguments
            # is this a function? call it
            if not inputs:
                api.output.verbose_msg(
                    ["scanner.scandirectory", "scanner"], "{} is none, skipping!".format(builder))
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
            api.output.verbose_msg(["scanner.directory.builder", "scanner.directory",
                                   "scanner.scandirectory", "scanner"], f"calling builder {builder}")
            out = func(allow_duplicates=True, _PARTS_DYN=True, **args)
            api.output.verbose_msg(["scanner.directory.builder", "scanner.directory", "scanner.scandirectory",
                                   "scanner"], f"Builder {builder} added {out} nodes")
            #api.output.verbose_msg(["scanner.scandirectory", "scanner"], "Adding nodes {0}".format([str(o) for o in out]))
            results += out

        callbacks = env.get("SCANDIR_CALLBACKS", scan_callbacks)

        for callback in callbacks:
            callback(node, env)
        env['allow_duplicates'] = v1
        env['_PARTS_DYN'] = v2
        del env['_DYNSCANNER_NODE']
        api.output.verbose_msgf(["scanner.scandirectory", "scanner", "scanner-results"],
                                "Scanning results {0}", [str(r) for r in results])

        if scan_results:  # have to have some data, else this is probally bad
            cache[node.ID] = scan_results

    return scan_results


##############################
# Default mapping functions

# scanner for common items
bin_scan = dict(
    InstallBin=dict(
        source=lambda node, env, default=None: [
            env.Pattern(src_dir=node.Dir("bin"),
                        includes=env["INSTALL_BIN_PATTERN"]),
            env.Pattern(src_dir=node.Dir("bin32"),
                        includes=env["INSTALL_BIN_PATTERN"]),
            env.Pattern(src_dir=node.Dir("bin64"),
                        includes=env["INSTALL_BIN_PATTERN"]),
        ]
    )
)
sbin_scan = dict(
    InstallSystemBin=dict(
        source=lambda node, env, default=None: [
            env.Pattern(src_dir=node.Dir("sbin"),
                        includes=env["INSTALL_BIN_PATTERN"]),
        ]
    )
)
lib_scan = dict(
    InstallLib=dict(
        source=lambda node, env, default=None: [
            env.Pattern(src_dir=node.Dir(
                "lib"), includes=env["INSTALL_LIB_PATTERN"] + env["INSTALL_API_LIB_PATTERN"]),
            env.Pattern(src_dir=node.Dir(
                "lib32"), includes=env["INSTALL_LIB_PATTERN"] + env["INSTALL_API_LIB_PATTERN"]),
            env.Pattern(src_dir=node.Dir(
                "lib64"), includes=env["INSTALL_LIB_PATTERN"] + env["INSTALL_API_LIB_PATTERN"]),
        ],
    )
)
pkgconfig_scan = dict(
    InstallPkgConfig=dict(
        source=lambda node, env, default=None: [
            env.Pattern(src_dir=node.Dir("lib/pkgconfig"), includes=["*.pc"]),
            env.Pattern(src_dir=node.Dir(
                "lib32/pkgconfig"), includes=["*.pc"]),
            env.Pattern(src_dir=node.Dir(
                "lib64/pkgconfig"), includes=["*.pc"]),
        ],
    )
)

cmakeconfig_scan = dict(
    InstallCMakeConfig=dict(
        source=lambda node, env, default=None: [
            env.Pattern(src_dir=node.Dir("lib/cmake"), includes=["*"]),
            env.Pattern(src_dir=node.Dir(
                "lib32/cmake"), includes=["*"]),
            env.Pattern(src_dir=node.Dir(
                "lib64/cmake"), includes=["*"]),
        ],
    )
)

include_scan = dict(
    InstallInclude=dict(
        source=lambda node, env, default=None: [
            env.Pattern(src_dir=node.Dir("include"), includes=[
                        "*.h", "*.H", "*.hxx", "*.hpp", "*.hh"]),
            env.Pattern(src_dir=node.Dir("include32"), includes=[
                        "*.h", "*.H", "*.hxx", "*.hpp", "*.hh"]),
            env.Pattern(src_dir=node.Dir("include64"), includes=[
                        "*.h", "*.H", "*.hxx", "*.hpp", "*.hh"]),
        ],
    )
)

etc_scan = dict(
    InstallConfig=dict(
        source=lambda node, env, default=None: [
            env.Pattern(src_dir=node.Dir("etc"), includes=["*"]),
        ],
    ),
)

libexec_scan = dict(
    InstallLibExec=dict(
        source=lambda node, env, default=None: [
            env.Pattern(src_dir=node.Dir("libexec"), includes=["*"]),
        ],
    ),
)
manpage_scan = dict(
    InstallManPage=dict(
        source=lambda node, env, default=None: [
            env.Pattern(src_dir=node.Dir("share/man"), includes=["*"]),
        ],
    ),
)
doc_scan = dict(
    InstallDoc=dict(
        source=lambda node, env, default=None: [
            env.Pattern(src_dir=node.Dir("share/doc"), includes=["*"]),
        ],
    ),
)
message_scan = dict(
    InstallMessage=dict(
        source=lambda node, env, default=None: [
            env.Pattern(src_dir=node.Dir("share/nls"), includes=["*"]),
        ],
    ),
)
data_scan = dict(
    InstallData=dict(
        source=lambda node, env, default=None: [
            env.Pattern(src_dir=node.Dir("share/"),
                        includes=["*"], excludes=['nls/*', 'man/*', 'doc/*']),
        ],
    ),
)

##############################


def ScanDirectory(env, default_dir, defaults=True, callbacks=[], extra_scanner=None, **builders):
    '''
    This returns a scanner to the scan a directory. It also calls a builder to a dyn.jsn file
    to help allow control flow of imported variable and depends handling in the taskmaster
    '''

    default_dir = env.arg2nodes(default_dir, env.Dir)
    use_scan_defaults = defaults
    scan_callbacks = common.make_list(callbacks)
    scan_overrides = builders

    # some control to not scan for stuff that might take time and user might not care about

    default_mappings_dict = {}
    default_mappings_dict.update(bin_scan if not env.get(
        "DIRECTORYSCAN_NO_BIN", False) else {})
    default_mappings_dict.update(sbin_scan if not env.get(
        "DIRECTORYSCAN_NO_SBIN", False) else {})
    default_mappings_dict.update(lib_scan if not env.get(
        "DIRECTORYSCAN_NO_LIB", False) else {})
    default_mappings_dict.update(pkgconfig_scan if not env.get(
        "DIRECTORYSCAN_NO_PKGCONFIG", False) else {})
    default_mappings_dict.update(cmakeconfig_scan if not env.get(
        "DIRECTORYSCAN_NO_CMAKECONFIG", False) else {})
    default_mappings_dict.update(include_scan if not env.get(
        "DIRECTORYSCAN_NO_INCLUDE", False) else {})
    default_mappings_dict.update(etc_scan if not env.get(
        "DIRECTORYSCAN_NO_CONFIG", env.get("DIRECTORYSCAN_NO_ETC", False)) else {})
    default_mappings_dict.update(libexec_scan if not env.get(
        "DIRECTORYSCAN_NO_LIBEXEC", False) else {})
    default_mappings_dict.update(manpage_scan if not env.get(
        "DIRECTORYSCAN_NO_MANPAGE", False) else {})
    default_mappings_dict.update(doc_scan if not env.get(
        "DIRECTORYSCAN_NO_DOC", False) else {})
    default_mappings_dict.update(message_scan if not env.get(
        "DIRECTORYSCAN_NO_MESSAGE", False) else {})
    default_mappings_dict.update(data_scan if not env.get(
        "DIRECTORYSCAN_NO_DATA", False) else {})

    # this generates the name of the side effect jsn file that stores state about what this scanned
    # having this data may not prove useful beyond debugging. however the file defines a known
    # pathway for everything to scan correctly on incremental builds. This is done via having
    # a set of state files that map imported and exported builder between components. This allows
    # the task logic to find and call the scanner to define nodes and or environment values to allow
    # the scanners and builder to work correctly when values are subst()
    md5 = hashlib.md5()
    md5.update(default_dir[0].ID.encode())
    name_hash = md5.hexdigest()
    state_file_name = env.File(
        "${{PARTS_SYS_DIR}}/${{PART_ALIAS}}.${{PART_SECTION}}.dyn.scan.{}.jsn".format(name_hash))
    default_dir[0].attributes._is_dyn_generated = True
    env.SideEffect(state_file_name, default_dir)
    env.Clean(default_dir, default_dir)
    # because we know this is dynamic we need to define
    # that the dyn.scan.{hash}.jsn need to be generated as a source to the dyn.exports.jsn file
    # the scanner will call a builder that will cause this file to be generated.
    # the existence of this file and environment variable allow us to know the exports are not fully known
    # yet for the section defining this parts.
    # As note.. The engine will check export_file node for sources to define that we have dynamic exports
    # I hope this should allow for a generic way for other "dynamic" builders to be defined as all we have to
    # do is add a new node to be built and used as a source to this dyn export file builder.
    #export_file = env._map_dyn_export_(default_dir)
    export_file = env._map_export_(
        [
            default_dir,
            state_file_name
        ]
    )

    # this allow us to have a quick way in the mappers that it is safe to cache the resulting subst() call
    # by checking that this file node is built
    glb.engine._part_manager.section_from_env(
        env).Env["DYN_EXPORT_FILE"] = env["DYN_EXPORT_FILE"] = export_file[0]
    glb.engine._part_manager.section_from_env(env).hasDynamicExports = True
    #
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
        # path_function=DynScanPath,
        argument=extras
    )


api.register.add_method(ScanDirectory)
