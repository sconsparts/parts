
import zipfile
import os
import SCons.Script
import parts.api as api


def _get_file_entries(node):
    # walk the Dir node to see what nodes it contains
    # return a flat list of file node
    ret = []
    for k, v in node.entries.viewitems():
        if isinstance(v, SCons.Node.FS.Dir) and k != ".." and k != ".":
            ret.extend(_get_file_entries(v))
        else:  # this is a File node
            ret.append(v)
    return ret


def zip(target, source, env):
    zf = zipfile.ZipFile(str(target[0]), 'w', zipfile.ZIP_DEFLATED)
    bd = env.Dir(env.subst('$BUILD_DIR')).abspath
    sd = env.Dir(env.subst('$SRC_DIR')).abspath
    root_dir = env.get('src_dir', None)

    def write_file(fnode):
        tmp = fnode.abspath
        if root_dir:
            t = tmp[len(root_dir):]
            zf.write(tmp, t)
        else:
            if tmp.startswith(bd):
                t = tmp[len(bd):]
                zf.write(tmp, t)
            elif tmp.startswith(sd):
                t = tmp[len(sd):]
                zf.write(tmp, t)
            else:
                zf.write(tmp)

    if root_dir:
        root_dir = env.Dir('$SRC_DIR').Dir(env.subst(root_dir)).abspath
    for s in source:

        if isinstance(s, SCons.Node.FS.Dir):
            # for a directory we have to get any extra nodes that would be in the directory.
            # we assume that the SCons has that everything in the build directory up-to-date
            # before it is called. Generally safe assumtion.
            files = _get_file_entries(s)
            for f in files:
                write_file(f)
        else:
            write_file(s)
    zf.close()


def CCopyStringFunc(target, source, env):
    return "Creating Zip file: {} containing {} files ".format(target[0], len(source))

ZipAction = SCons.Action.Action(zip, CCopyStringFunc, varlist=['BUILD_DIR', 'SRC_DIR', 'src_dir'])

api.register.add_builder('ZipFile', SCons.Builder.Builder(action=ZipAction,
                                                          source_factory=SCons.Node.FS.Entry,
                                                          source_scanner=SCons.Defaults.DirScanner,
                                                          suffix='.zip', multi=1))
