import os
import tarfile
import SCons.Script
import parts.api as api


def tar(target, source, env, type):

    # this code makes a seperate File handle directly
    # as it was discovered that the tarfile logic will add the subdirectories
    # to the current directory for the main archive as a "feature"
    # this mean the build/variant directory will show up
    fobj = open(str(target[0]), 'wb')
    # By doing it this way remove this extra data so it does not show up
    # Note this is more of an issue for windows than linux, as classic linux
    # tools will not show the extra data.
    zf = tarfile.open(name=os.path.split(target[0].path)[1], fileobj=fobj, mode=type)
    bd = env.Dir(env.subst('$BUILD_DIR')).abspath
    sd = env.Dir(env.subst('$SRC_DIR')).abspath
    root_dir = env.get('src_dir', None)
    if root_dir is not None:
        root_dir = env.Dir('$SRC_DIR').Dir(env.subst(root_dir)).abspath
    for s in source:
        tmp = s.abspath
        if root_dir is not None:
            t = tmp[len(root_dir):]
            zf.add(tmp, t)
        else:
            if tmp.startswith(bd):
                t = tmp[len(bd):]
                zf.add(tmp, t)
            elif tmp.startswith(sd):
                t = tmp[len(sd):]
                zf.add(tmp, t)
            else:
                zf.add(tmp)
    zf.close()
    fobj.close()
    # tar=tarfile.open(source,'r')
    # tar.extractall(destination)
    # tar.close()


def CCopyStringFunc(target, source, env):
    return "Creating Achieve file: {} containing {} files ".format(target[0], len(source))


TarAction = SCons.Action.Action(lambda target, source, env: tar(target, source, env, 'w'),
                                CCopyStringFunc, varlist=['BUILD_DIR', 'SRC_DIR'])
GzAction = SCons.Action.Action(lambda target, source, env: tar(target, source, env, 'w|gz'),
                               CCopyStringFunc, varlist=['BUILD_DIR', 'SRC_DIR'])
bz2Action = SCons.Action.Action(lambda target, source, env: tar(target, source, env, 'w|bz2'),
                                CCopyStringFunc, varlist=['BUILD_DIR', 'SRC_DIR'])

api.register.add_builder('TarFile', SCons.Builder.Builder(action=TarAction,
                                                          source_factory=SCons.Node.FS.Entry,
                                                          source_scanner=SCons.Defaults.DirScanner,
                                                          suffix='.tar', multi=1))

api.register.add_builder('GzFile', SCons.Builder.Builder(action=GzAction,
                                                         source_factory=SCons.Node.FS.Entry,
                                                         source_scanner=SCons.Defaults.DirScanner,
                                                         suffx='.tar.gz', multi=1))

api.register.add_builder('Bz2File', SCons.Builder.Builder(action=bz2Action,
                                                          source_factory=SCons.Node.FS.Entry,
                                                          source_scanner=SCons.Defaults.DirScanner,
                                                          suffix='.bz2', multi=1))

api.register.add_builder('TarBz2File', SCons.Builder.Builder(action=bz2Action,
                                                             source_factory=SCons.Node.FS.Entry,
                                                             source_scanner=SCons.Defaults.DirScanner,
                                                             suffix='.tar.bz2', multi=1))

api.register.add_builder('TgzFile', SCons.Builder.Builder(action=GzAction,
                                                          source_factory=SCons.Node.FS.Entry,
                                                          source_scanner=SCons.Defaults.DirScanner,
                                                          suffx='.tgz', multi=1))

api.register.add_builder('TarGzFile', SCons.Builder.Builder(action=GzAction,
                                                            source_factory=SCons.Node.FS.Entry,
                                                            source_scanner=SCons.Defaults.DirScanner,
                                                            suffx='.tar.gz', multi=1))

api.register.add_builder('Tbz2File', SCons.Builder.Builder(action=bz2Action,
                                                           source_factory=SCons.Node.FS.Entry,
                                                           source_scanner=SCons.Defaults.DirScanner,
                                                           suffix='.tbz2', multi=1))
