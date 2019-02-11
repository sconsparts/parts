
from __future__ import absolute_import, division, print_function

import os
import subprocess

import parts.api as api
import parts.common as common
import parts.core.util as util

import SCons.Defaults
import SCons.Script


def rpath_emit(target, source, env):
    new_target = []
    for t in source:
        if util.isSymLink(t):
            new_target.append(env.Dir("_set_RPATH_").FileSymbolicLink(t.name))
        else:
            new_target.append(env.Dir("_set_RPATH_").File(t.name))
    return (new_target, source)


# basically for system that don't have rpath logic.. just copy to avoid breaking stuff
copy_rpath_action = SCons.Defaults.Copy('$TARGET', '$SOURCE')

set_rpath_action = SCons.Action.Action([copy_rpath_action, 'patchelf --set-rpath $RUNPATH_STR $TARGET'])
remove_rpath_action = SCons.Action.Action([copy_rpath_action, 'patchelf --remove-rpath $TARGET'])


def _is_text(node):
    try:
        text = subprocess.check_output(['file', node.abspath]).decode()
        if "text" in text:
            return True
    except:
        pass
    return False


def _is_binary(node):
    if util.isFile(node) and\
            not util.isSymLink(node) and\
            not os.path.islink(node.abspath) and\
            not _is_text(node):
        return True
    return False

# requires patchelf as this works better


def set_rpath_func(target, source, env):
    dynamic_actions = None
    source[0].disambiguate()
    rpath = common.make_list(
        env.get("PACKAGE_RUNPATH", [])
    )
    api.output.verbose_msgf(['SetRPath'], "PACKAGE_RUNPATH = {0}", rpath)
    # check the source as the target does not exist yet
    if not _is_binary(source[0]):
        api.output.verbose_msgf(['SetRPath'], "{0} is not a binary", target[0])
        dynamic_actions = copy_rpath_action
    # if set to None remove ( This has to be set by user)
    elif rpath is None:
        api.output.verbose_msgf(['SetRPath'], "Removing runpath from {0}", target[0])
        dynamic_actions = remove_rpath_action
    # if it has values change binaries
    elif rpath:
        rpath_str = ":".join(rpath)
        env['RUNPATH_STR'] = rpath_str
        api.output.verbose_msgf(['SetRPath'], "Changing runpath for {0} to {1}", target[0], rpath_str)
        dynamic_actions = set_rpath_action
    else:
        api.output.verbose_msgf(['SetRPath'], "Doing basic copy {0}", target[0])
        dynamic_actions = copy_rpath_action

    return dynamic_actions(target, source, env)


set_runpath_action = SCons.Action.Action(set_rpath_func, None)

# internal rpm package builder... meant to be called by RPMPackage function internally
api.register.add_builder('SetRPath', SCons.Builder.Builder(
    emitter=rpath_emit,
    action=set_runpath_action,
    single_source=True
)
)
