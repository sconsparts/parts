"""
this tool override is provided as a way to support the a hock we need to deal
with libraries on linux that use symlinks. this add a hack support to unpack file
on copy... hopefully this can be dropped soon once i get time to make a better solution
"""


import fnmatch
import os
from builtins import map, zip

import parts.core.scanners as scanners
import parts.core.util as util
import parts.core.builders.ccopy as ccopy
import parts.overrides.symlinks as symlinks
import SCons.Action
import SCons.Errors
# We keep track of *all* installed files.
import SCons.Tool.install
from parts.common import make_list
from SCons.Debug import logInstanceCreation
from SCons.Util import make_path_relative

'''def installFunc(target, source, env):
    """
    Install a source file into a target using the function specified
    as the INSTALL construction variable.
    """

    try:
        install = env['INSTALL']
    except KeyError:
        raise SCons.Errors.UserError('Missing INSTALL construction variable.')

    assert len(target) == len(source), \
        ("Installing source %s into target %s: target and source lists must have same "
         "length.") % (list(map(str, source)), list(map(str, target)))

    # get the logger for a given Part if it exists
    output = env._get_part_log_mapper()
    # tell it we are starting a task
    taskId = output.TaskStart(stringFunc(target, source, env) + "\n")

    for targetEntry, sourceEntry in zip(target, source):
        if isinstance(sourceEntry, symlinks.FileSymbolicLink):
            assert sourceEntry.exists() and sourceEntry.linkto
            # A symbolic link can only be a copy of another symlink.
            # Convert a source node to SymLink this is needed for
            # correct up-to-date checks during incremental builds
            symlinks.ensure_node_is_symlink(targetEntry)
            if targetEntry.linkto is None:
                targetEntry.linkto = sourceEntry.linkto
            if symlinks.make_link_bf([targetEntry], [targetEntry.Entry(targetEntry.linkto)],
                                     env):
                output.TaskEnd(taskId, 1)
                return 1
            continue

        if install(targetEntry.get_path(), sourceEntry.get_path(), env):
            output.TaskEnd(taskId, 1)
            # report error to logger
            return 1
    # tell logger the task has end correctly.
    output.TaskEnd(taskId, 0)
    return 0
'''


def stringFunc(target, source, env):
    installstr = env.get('INSTALLSTR')
    if installstr:
        return env.subst_target_source(installstr, 0, target, source)
    target = str(target[0])
    source = str(source[0])
    targetType = 'directory' if os.path.isdir(source) else 'file'
    return 'Install %s: "%s" as "%s"' % (targetType, source, target)

# auto tagging


def auto_tag(env, node):
    if env.get("AUTO_TAG_ON_INSTALL", True):
        for patterns, tags in env.get("AUTO_TAG_INSTALL", []):
            patterns = make_list(patterns)
            for pattern in patterns:
                if fnmatch.fnmatchcase(str(node), pattern):
                    env.MetaTag(node, 'package', **tags)

#
# Emitter functions
#


def add_targets_to_INSTALLED_FILES(target, source, env):
    """
    an emitter that adds all target files to the list stored in the
    _INSTALLED_FILES global variable. This way all installed files of one
    scons call will be collected.
    """
    tags = env.get('tags', {})
    # add to global list of install files
    for targetEntry in target:
        # add meta tags
        if tags:
            env.MetaTag(targetEntry, 'package', **tags)
        # see if the file should be auto taged based on value
        auto_tag(env, targetEntry)
        # sort into list is it has not been set with package::no_package tag
        no_pkg = env.MetaTagValue(targetEntry, 'no_package', 'package', False)
        # don't add No package tagged items to the installed files list
        if not no_pkg:
            SCons.Tool.install._INSTALLED_FILES.append(targetEntry)

    return target, source


class DESTDIR_factory:
    """
    a node factory, where all files will be relative to the dir supplied in the constructor.
    """

    def __init__(self, env, destDir):
        if __debug__:
            logInstanceCreation(self)
        self.env = env
        self.dir = env.arg2nodes(destDir, env.fs.Dir)[0]

    def Entry(self, name):
        name = make_path_relative(name)
        return self.dir.Entry(name)

    def Dir(self, name):
        name = make_path_relative(name)
        return self.dir.Dir(name)


#
# The Builder Definition
#

install_action = SCons.Action.Action(
    '${TEMPFILE("parts-smart-cp --sources $($CHANGED_SOURCES $) --targets $($CHANGED_TARGETS $) --copy-only=$_COPY_ONLY_ --verbose=$($_CCOPY_VERBOSE_ $)")}',
    stringFunc,  
    batch_key=ccopy.batch_key
)
installas_action = SCons.Action.Action(
    '${TEMPFILE("parts-smart-cp --sources $($CHANGED_SOURCES $) --targets $($CHANGED_TARGETS $) --copy-only=$_COPY_ONLY_ --verbose=$($_CCOPY_VERBOSE_ $)")}',
    stringFunc,
    batch_key=ccopy.batch_key
)

#install_action = SCons.Action.Action(installFunc, stringFunc)
#installas_action = SCons.Action.Action(installFunc, stringFunc)

BaseInstallBuilder = None


def InstallBuilderWrapper(env, target=None, source=None, targetDir=None, **kw):
    if target and targetDir:
        raise SCons.Errors.UserError("Both target and dir defined for Install(), "
                                     "only one may be defined.")
    if "CCOPY_BATCH_KEY" not in kw:
        kw['CCOPY_BATCH_KEY'] = ccopy.make_batch_value(env.get_csig_hash())
    if not targetDir:
        targetDir = target

    target_factory = env.fs

    try:
        dnodes = env.arg2nodes(targetDir, target_factory.Dir)
    except TypeError:
        raise SCons.Errors.UserError(("Target `%s' of Install() is a file, but should be a "
                                      "directory. Perhaps you have the Install() arguments "
                                      "backwards?") % targetDir)
    sources = env.arg2nodes(source, env.fs.Entry)

    tgt = []
    for dnode in dnodes:
        for src in sources:
            # Prepend './' so the lookup doesn't interpret an initial
            # '#' on the file name portion as meaning the Node should
            # be relative to the top-level SConstruct directory.
            if util.isDir(src):
                target = env.fs.Dir(os.sep.join(['.', src.name]), dnode)
            else:
                target = env.fs.Entry(os.sep.join(['.', src.name]), dnode)
            if util.isSymLink(src):
                symlinks.ensure_node_is_symlink(target, src.linkto)
            # call emiter
            nenv = env.Override(kw)
            t, s = add_targets_to_INSTALLED_FILES([target], [src], nenv)
            tgt.extend(
                BaseInstallBuilder(
                    env,
                    target,
                    src,
                    _COPY_ONLY_="True",
                    _CCOPY_VERBOSE_="True",
                    TEMPFILEPREFIX='-@',
                    **kw
                )
            )

    return tgt


def InstallAsBuilderWrapper(env, target=None, source=None, **kw):
    result = []
    if "CCOPY_BATCH_KEY" not in kw:
        kw['CCOPY_BATCH_KEY'] = ccopy.make_batch_value(env.get_csig_hash())
    for sourceEntry, targetEntry in zip(source, target):
        result.extend(
            BaseInstallBuilder(
                env,
                targetEntry,
                sourceEntry,
                _COPY_ONLY_="True",
                _CCOPY_VERBOSE_="True",
                TEMPFILEPREFIX='-@',
                **kw
            )
        )

    return result


def generate(env):
    global BaseInstallBuilder
    if BaseInstallBuilder is None:
        target_factory = env.fs

        BaseInstallBuilder = SCons.Builder.Builder(
            action=install_action,
            target_factory=target_factory.Entry,
            source_factory=env.fs.Entry,
            # don't want the install tool to calling global scanners
            target_scanner=symlinks.symlink_scanner,
            source_scanner=scanners.NullScanner,
            multi=1,
            emitter=[add_targets_to_INSTALLED_FILES, ],
            name='InstallBuilder'
        )

    #BaseInstallBuilder = lambda target, source, env, **kw: env.CCopyAs(target,source,**kw)

    env['BUILDERS']['_InternalInstall'] = InstallBuilderWrapper
    env['BUILDERS']['_InternalInstallAs'] = InstallAsBuilderWrapper

    # try:
    #    env['INSTALL']
    # except KeyError:
    #    env['INSTALL'] = copyFunction


def exists(env):
    return True

# vim: set et ts=4 sw=4 ai ft=python :
