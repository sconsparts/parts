

import os
import subprocess

import parts.glb as glb
import parts.core.builders.ccopy as ccopy
import parts.api as api
import parts.common as common
import parts.core.scanners as scanners
import parts.core.util as util
import parts.overrides.symlinks as symlinks
import SCons.Defaults
import SCons.Script



def rpath_emit(target, source, env):
    new_target = []
    prefixdir = env.Dir(env.get("RPATH_TARGET_PREFIX", "_set_RPATH_"))
    env['CCOPY_BATCH_KEY'] = (hash("SetRpath"), hash(env.subst("$PART_ALIAS")))
    for t in source:
        if util.isSymLink(t):
            new_target.append(prefixdir.FileSymbolicLink(t.name))
        else:
            new_target.append(prefixdir.File(t.name))
    return (new_target, source)


ccopy_action = SCons.Action.Action(  # [
    # meta_copy,
    '${TEMPFILE("parts-smart-cp --sources $($CHANGED_SOURCES $) --targets $($CHANGED_TARGETS $) --copy-only=True --verbose=$_CCOPY_VERBOSE_")}',
    # ],
    #cmdstr=f"parts-smart-cp --sources $CHANGED_SOURCES --targets $CHANGED_TARGETS --copy-only=$_COPY_ONLY_ --verbose=$_CCOPY_VERBOSE_",
    batch_key=ccopy.batch_key
)
# basically for system that don't have rpath logic.. just copy to avoid breaking stuff
#copy_rpath_action = SCons.Defaults.Copy('$TARGET', '$SOURCE')
copy_rpath_action = ccopy_action


set_rpath_action = SCons.Action.Action([copy_rpath_action, 'patchelf --set-rpath $RUNPATH_STR $TARGET'])
remove_rpath_action = SCons.Action.Action([copy_rpath_action, 'patchelf --remove-rpath $TARGET'])


def _is_elf(node):
    try:
        text = subprocess.check_output(['file', node.abspath]).decode()
        # hardcoding in object files to not be viewed as true
        # need to do something better for these cases later.
        if " ELF " in text and not node.ID.endswith((".o",".obj")):
            return True
    except Exception:
        pass
    return False


def _is_binary(node):
    if util.isFile(node) and _is_elf(node):
        return True
    return False

# requires patchelf as this works better


def set_rpath_func(target, source, env):
    env['_CCOPY_VERBOSE_'] = 'True' if 'ccopy' in glb.rpter.verbose else 'True' if 'all' in glb.rpter.verbose else 'False'
    dynamic_actions = None

    rpath = common.make_list(
        env.get("PACKAGE_RUNPATH", [])
    )
    auto_rpath = env.get("PACKAGE_AUTO_RUNPATH", True)
    api.output.verbose_msgf(['SetRPath'], "PACKAGE_RUNPATH = {0} PACKAGE_AUTO_RUNPATH={1}", rpath, auto_rpath)
    # check the source as the target does not exist yet
    if not _is_binary(source[0]):
        api.output.verbose_msgf(['SetRPath'], "{0} is not a binary", target[0])
        dynamic_actions = copy_rpath_action
    # if set to None remove ( This has to be set by user)
    elif rpath is None:
        api.output.verbose_msgf(['SetRPath'], "Removing runpath from {0}", target[0])
        dynamic_actions = remove_rpath_action
    # if it has values change binaries
    elif rpath or auto_rpath:

        newpath = env.subst("$RUNPATH_STR")
        if newpath:
            api.output.verbose_msgf(['SetRPath'], "Changing runpath for {0} to '{1}'",
                                    target[0], common.DelayVariable(lambda: env.subst("$RUNPATH_STR")))
            dynamic_actions = set_rpath_action
        else:
            api.output.warning_msgf(
                "Finial runpath value is empty, Skipping any modification to binary '{0}'", target[0], show_stack=False)
            api.output.verbose_msgf(['SetRPath'], "Doing basic copy {0}", target[0])
            dynamic_actions = copy_rpath_action

    else:
        api.output.verbose_msgf(['SetRPath'], "Doing basic copy {0}", target[0])
        dynamic_actions = copy_rpath_action

    return dynamic_actions(target, source, env)


set_runpath_action = SCons.Action.Action(set_rpath_func, None)

api.register.add_variable(
    "_PACKAGE_RUNPATH",
    ["$PACKAGE_RUNPATH"],
    ""
)
api.register.add_variable(
    "RUNPATH_STR",
    "${JOIN('$_PACKAGE_RUNPATH',':')}",
    ""
)

# internal rpm package builder... meant to be called by RPMPackage function internally
api.register.add_builder(
    'SetRPath',
    SCons.Builder.Builder(
        emitter=rpath_emit,
        action=set_runpath_action,
        single_source=True,
        target_scanner=symlinks.symlink_scanner,
        source_scanner=scanners.NullScanner,
        name="set-rpath"
    )
)
