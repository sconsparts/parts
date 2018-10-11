import itertools
import os
import shutil
import tempfile

import parts.api as api
import parts.common as common
import parts.core.util as util
import parts.errors
import parts.glb as glb

import SCons.Script

MACRO_STARTS = ('%description', '%prep', '%check', '%build', '%install', '%clean', '%files')


def is_macro_header(line):
    return any(line.startswith(start) for start in MACRO_STARTS)


def add_install_content(env, file_contents):
    deflines = [
        '%install',
        'mkdir -p %{buildroot}',
        'cp -a * %{buildroot}'
    ]

    # add default install contents
    for line in deflines:
        file_contents.append(line)


def add_prep_content(env, file_contents, prefix):
    deflines = ['%install', 'setup -q']

    # add default install contents
    for line in deflines:
        file_contents.append(line)


def add_files_content(env, file_contents, pkg_files, prefix, idx=-1):
    # add all content in archive file
    defattrs = '%defattr(-,root,root,-)'

    # the directories we add under the package root
    directories = set()
    # the file we add
    files = []

    repstr = env.subst('${RPM_BUILD_ROOT}').lstrip('#')
    for node in pkg_files:
        tmp = node.ID.replace(repstr, '')
        if util.isFile(node):
            dir_tmp = '%dir {0}'.format(os.path.split(tmp)[0])
            directories.add(dir_tmp)
            if env.hasMetaTag(node, 'POSIX_ATTR') or env.hasMetaTag(node, 'POSIX_USER') or env.hasMetaTag(node, 'POSIX_GROUP'):
                attr = env.MetaTagValue(node, 'POSIX_ATTR', default="-")
                user = env.MetaTagValue(node, 'POSIX_USER', default="-")
                group = env.MetaTagValue(node, 'POSIX_GROUP', default="-")
                tmp = '%attr({attr},{user},{group}) {node}'.format(attr=attr, user=user, group=group, node=tmp)
            files.append(tmp)
        else:
            if env.hasMetaTag(node, 'POSIX_ATTR') or env.hasMetaTag(node, 'POSIX_USER') or env.hasMetaTag(node, 'POSIX_GROUP'):
                attr = env.MetaTagValue(node, 'POSIX_ATTR', default="-")
                user = env.MetaTagValue(node, 'POSIX_USER', default="-")
                group = env.MetaTagValue(node, 'POSIX_GROUP', default="-")
                dir_tmp = '%dir %attr({attr},{user},{group}) {node}'.format(attr=attr, user=user, group=group, node=tmp)
            else:
                dir_tmp = '%dir {0}'.format(tmp)
            directories.add(dir_tmp)

    # if files section does not exist
    if idx == -1:
        api.output.verbose_msg(['rpm-spec'], "Generating %file section")
        file_contents.append('\n')
        file_contents.append('%files')
        # add default attributes
        file_contents.append(defattrs)

        # directories
        for node in itertools.chain(files, directories):
            api.output.verbose_msg(['rpm-spec'], " {0}".format(node))
            file_contents.append(node)
    else:
        api.output.verbose_msg(['rpm-spec'], "Adding to %file section")
        # add default attributes
        file_contents.insert(idx + 1, defattrs)
        # directories
        for i, node in enumerate(itertools.chain(files, directories)):
            api.output.verbose_msg(['rpm-spec'], " {0}".format(node))
            file_contents.insert(idx + 2 + i, node)


def rpm_spec(env, target, source):

    # these are set from rpm_package wrapper function
    target_name = env['NAME']
    target_version = env['VERSION']
    target_release = env['RELEASE']
    pkg_files = env['PKG_FILES']
    # list of custom vars to add
    rpm_vals = env.get('RPM_VARS',[])

    if not rpm_spec:
        api.output.verbose_msg(['rpm-spec'], "No custom RPM spec variables added")
    else:
        new_vals=[]
        for v in rpm_vals:
            try:
                new_vals.append(env.subst(v))
            except:
                api.output.warning_msgf("Failed to subst() value:\n {0}\n passing orginal value instead.",v)
                new_vals.append(v)
        rpm_vals=new_vals

    # open spec file
    with open(source[0].abspath, 'r') as file_obj:
        file_contents = file_obj.read().split('\n')

    # If BuildArch exists in specfile, delete the line
    # It will take host architecture as the build architecture by default
    file_contents = filter(lambda x: not x.startswith('BuildArch'),
                           file_contents)

    # override some value to match name of out rpm files.
    found_install = False
    found_files = False
    found_prep = False

    # default rpm prefix value
    prefix = '/usr'

    # make this all the api.output...
    api.output.print_msg("Overriding the spec file values for name, version, release")
    i = 0
    # tmp set to detect duplicates of values that should only be defined once
    tmp = set(('name', 'version', 'release'))

    while i < len(file_contents):

        if file_contents[i].startswith('Name'):
            file_contents[i] = 'Name:' + target_name
            try:
                tmp.remove('name')
            except KeyError:
                pass

        elif file_contents[i].startswith('Version'):
            file_contents[i] = 'Version:' + target_version
            try:
                tmp.remove('version')
            except KeyError:
                pass

        elif file_contents[i].startswith('Prefix'):
            prefix = file_contents[i].split(":")[1].strip()

        elif file_contents[i].startswith('Release'):
            file_contents[i] = 'Release:' + target_release
            try:
                tmp.remove('release')
            except KeyError:
                pass

        elif file_contents[i].startswith('%install'):
            found_install = True

        elif file_contents[i].startswith('%prep'):
            found_prep = True

        # add file contents that will be installed in rpm
        elif file_contents[i].startswith('%files'):
            found_files = True
            add_files_content(env, file_contents, pkg_files, prefix, i)

        i += 1

    # add sections if they do not exist
    if not found_install:
        add_install_content(env, file_contents)

    if not found_prep:
        add_prep_content(env, file_contents, prefix)

    if not found_files:
        add_files_content(env, file_contents, pkg_files, prefix)

    if tmp:
        api.output.warning_msg("Did not find keys value in spec file for {0}".format(", ".join(tmp)))

    # If BuildArch exists in specfile, delete the line
    # It will take host architecture as the build architecture by default
    if rpm_vals:
        file_contents = rpm_vals + file_contents
    file_contents = "\n".join(file_contents) + '\n'
    with open(target[0].abspath, 'wb') as out_file:
        out_file.write(file_contents)


rpmspec_action = SCons.Action.Action(rpm_spec)

api.register.add_builder('_rpmspec', SCons.Builder.Builder(
    action=rpmspec_action,
    source_factory=SCons.Node.FS.File,
    target_factory=SCons.Node.FS.File
))
