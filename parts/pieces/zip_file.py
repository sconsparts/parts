
import zipfile
import os
import SCons.Script
import parts.api as api


def zip(target, source, env):
    zf = zipfile.ZipFile(str(target[0]), 'w',zipfile.ZIP_DEFLATED)
    bd = env.Dir(env.subst('$BUILD_DIR')).abspath
    sd = env.Dir(env.subst('$SRC_DIR')).abspath
    root_dir = env.get('src_dir',None)    
    if root_dir:
        root_dir = env.Dir('$SRC_DIR').Dir(env.subst(root_dir)).abspath
    for s in source:
        tmp = s.abspath
        if root_dir:
            t = tmp[len(root_dir):]
            zf.write(tmp,t)
        else:
                
            if tmp.startswith(bd):
                t = tmp[len(bd):]
                zf.write(tmp,t)
            elif tmp.startswith(sd):
                t = tmp[len(sd):]
                zf.write(tmp,t)
            else:
                zf.write(tmp)
    zf.close()


ZipAction = SCons.Action.Action(zip, varlist=['BUILD_DIR', 'SRC_DIR', 'src_dir'])

api.register.add_builder('ZipFile',SCons.Builder.Builder(action = ZipAction,
                                   source_factory = SCons.Node.FS.Entry,
                                   source_scanner = SCons.Defaults.DirScanner,
                                   suffix = '.zip',multi = 1))
