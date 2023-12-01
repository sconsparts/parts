from typing import List, Optional
import parts.api as api
import parts.core.scanners as scanners
import parts.common as common
import parts.pattern as pattern


# this is basically calling another builder with a different target and key values

def PkgConfigUninstallFunc(env, target, source, from_prefix:str, to_prefix:str, **kw):
    """
    Replaces the target with the uninstalled target for each source file.
    This is generally used to replace the prefix in the pkg-config file.
    Will normally be called by the SDK/Install functions and not directly.
    
    Args:
        env: The environment object.
        source: The source file(s) to process.
        from_prefix: The prefix to replace with the to_prefix.
        to_prefix: The prefix to use in the prefix values.

    Returns:
        A list of modified target file(s).
    """
    
    ret = []
    subst_dict = {env.Dir(from_prefix).abspath:env.Dir(to_prefix).abspath}
    # convert the target to a node
    target = env.arg2nodes(target, env.fs.Dir)
    if len(target) != 1:
        api.output.error_msg("Target must be a single file")

    # just want the single node
    target_node = target[0]
    # make sure the source is a list of sources
    sources = common.make_list(source)
    
    for node in sources:
        if isinstance(node, pattern.Pattern):
            # in this case we need to get the files from the pattern as the target is generated from this source file name
            sr = node.files()
            for s in sr:
                fname = s.name[:-3]  # this is the base name of the file
                ret += env.Substfile(target=target_node.File(fname+"-uninstalled.pc"), source=s, SUBST_DICT=subst_dict, **kw)
            
        else: # this is a node vs pattern
            node = env.arg2nodes(node, env.fs.File)[0]
            fname = node.name[:-3] # this is the base name of the file
            ret += env.Substfile(target=target_node.File(fname+"-uninstalled.pc"), source=node, SUBST_DICT=subst_dict, **kw)
    return ret

api.register.add_method(PkgConfigUninstallFunc, "PkgConfigUninstall")