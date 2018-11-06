from __future__ import absolute_import, division, print_function

import os

import parts.tools.Common

import SCons.Node.FS
from Common.java import java
from SCons.Node.FS import _my_normcase
from SCons.Tool import javac
from SCons.Tool.JavaCommon import parse_java_file

# monkey patch emit_java_classes to do the Right Thing
# otherwise generated classes have no package name and get rebuilt always


def emit_java_classes(target, source, env):
    """
    Set correct path for .class files from generated java source files
    """
    java_suffix = env.get('JAVASUFFIX', '.java')
    class_suffix = env.get('JAVACLASSSUFFIX', '.class')

    target[0].must_be_same(SCons.Node.FS.Dir)
    classdir = target[0]

    if isinstance(source[0].disambiguate(), SCons.Node.FS.Dir):
        srcdir = source[0]
    else:
        srcdir = source[0].dir

    s = source[0].rentry().disambiguate()
    if isinstance(s, SCons.Node.FS.File):
        sourcedir = s.dir.rdir()
    elif isinstance(s, SCons.Node.FS.Dir):
        sourcedir = s.rdir()
    else:
        raise SCons.Errors.UserError("Java source must be File or Dir, not '%s'" % s.__class__)

    slist = []
    js = _my_normcase(java_suffix)
    for entry in source:
        entry = entry.rentry().disambiguate()
        if isinstance(entry, SCons.Node.FS.File):
            slist.append(entry)
        elif isinstance(entry, SCons.Node.FS.Dir):
            result = SCons.Util.OrderedDict()
            dirnode = entry.rdir()

            def find_java_files(arg, dirpath, filenames):
                java_files = sorted([n for n in filenames
                                     if _my_normcase(n).endswith(js)])
                mydir = dirnode.Dir(dirpath)
                java_paths = [mydir.File(f) for f in java_files]
                for jp in java_paths:
                    arg[jp] = True
            for dirpath, dirnames, filenames in os.walk(dirnode.get_abspath()):
                find_java_files(result, dirpath, filenames)
            entry.walk(find_java_files, result)

            slist.extend(list(result.keys()))
        else:
            raise SCons.Errors.UserError("Java source must be File or Dir, not '%s'" % entry.__class__)

    version = env.get('JAVAVERSION', '1.4')
    full_tlist = []
    for f in slist:
        tlist = []
        source_file_based = True
        pkg_dir = None
        if not f.is_derived():
            pkg_dir, classes = parse_java_file(f.rfile().get_abspath(), version)
            if classes:
                source_file_based = False
                if pkg_dir:
                    d = target[0].Dir(pkg_dir)
                    p = pkg_dir + os.sep
                else:
                    d = target[0]
                    p = ''
                for c in classes:
                    t = d.File(c + class_suffix)
                    t.attributes.java_classdir = classdir
                    t.attributes.java_sourcedir = sourcedir
                    t.attributes.java_classname = javac.classname(p + c)
                    tlist.append(t)

        if source_file_based:
            if pkg_dir:
                t = target[0].Dir(pkg_dir).File(class_suffix.join(f.name.rsplit(java_suffix, 1)))
            else:
                t = target[0].File(class_suffix.join(srcdir.rel_path(f).split(java_suffix, 1)))
            t.attributes.java_classdir = classdir
            t.attributes.java_sourcedir = f.dir
            t.attributes.java_classname = javac.classname(srcdir.rel_path(f.dir).split(java_suffix, 1)[0])
            tlist.append(t)

        for t in tlist:
            t.set_specific_source([f])

        full_tlist.extend(tlist)

    return full_tlist, slist


javac.emit_java_classes = emit_java_classes


def generate(env, *args, **kw):

    java.MergeShellEnv(env)

    javac.generate(env, *args, **kw)

    env['JAVAC'] = parts.tools.Common.toolvar('javac', env=env)


def exists(env):
    return javac.exists(env)

# vim: set et ts=4 sw=4 ai :
