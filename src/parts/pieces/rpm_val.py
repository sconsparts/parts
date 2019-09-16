from __future__ import absolute_import, division, print_function

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


def file_section_wrapper(env, key):
    pkg_files = env['PKG_FILES']
    prefix = add_if(env, "{value}", ('Prefix', 'X_RPM_PREFIX', 'PACKAGE_ROOT'), lambda env, key, value: value, None, True, True)
    items = []
    add_files_content(env, items, pkg_files, prefix)
    return "\n".join(items)+"\n\n"


def rpm_list_mapper(env, key, value):
    value = common.make_list(value)
    return ",".join(value)


# dictionary of all values needed or might be needed
# assume the "subst() happens before format() call"
headers = [
    # required
    dict(key='Name', value='{key}: {value}\n', required=True),
    dict(key='Version', value='{key}: {value}\n', required=True),
    dict(key='Release', value='{key}: {value}\n', required=True),
    dict(key='Group', extra_keys=('X_RPM_GROUP',), value='{key}: {value}\n', required=True),
    dict(key='Summary', value='{key}: {value}\n', required=True),
    dict(key='License', value='{key}: {value}\n', required=True),
    # Source is internal.. funky case
    dict(key='Source',
         value='Source0: %{{name}}-%{{version}}.tar.gz\n',
         default='Source0: %{{name}}-%{{version}}.tar.gz\n', required=True),
    # default to X_RPM_PREFIX first then PACKAGE_ROOT as this value is not
    dict(key='Prefix', extra_keys=('X_RPM_PREFIX', 'PACKAGE_ROOT'),
         value='{key}: {value}\n',
         default='{key}: ${{PACKAGE_ROOT}}\n',
         required=True),
    # optional
    dict(key='Url', extra_keys=('X_RPM_URL',), value='{key}: {value}\n',),
    dict(key='Distribution', extra_keys=('X_RPM_DISTRIBUTION',), value='{key}: {value}\n',),
    dict(key='Icon', extra_keys=('X_RPM_ICON',), value='{key}: {value}\n',),
    dict(key='Packager', extra_keys=('X_RPM_PACKAGER',), value='{key}: {value}\n',),
    dict(key='Requires', extra_keys=('X_RPM_REQUIRES',), value_mapper=rpm_list_mapper, value='{key}: {value}\n',),
    dict(key='BuildRequires', extra_keys=('X_RPM_BUILDREQUIRES',), value_mapper=rpm_list_mapper, value='{key}: {value}\n',),
    dict(key='Provides', extra_keys=('X_RPM_PROVIDES',), value_mapper=rpm_list_mapper, value='{key}: {value}\n',),
    dict(key='Conflicts', extra_keys=('X_RPM_CONFLICTS',), value='{key}: {value}\n',),
    dict(key='Epoch', extra_keys=('X_RPM_EPOCH',), value='{key}: {value}\n',),
    dict(key='AutoReqProv', extra_keys=('X_RPM_AUTOREQPROV',), value='{key}: {value}\n',),
    dict(key='AutoReq', extra_keys=('X_RPM_AUTOREQ',), value='{key}: {value}\n',),
    dict(key='AutoProv', extra_keys=('X_RPM_AUTOPROV',), value='{key}: {value}\n',),
]

sections = [
    dict(key='%description', value='{key}\n{value}\n\n', required=True),
    dict(key='%prep', extra_keys=('X_RPM_PREP',), value='{key}\n{value}\n\n', default='%prep\n%setup -q\n\n', required=True),
    dict(key='%build', extra_keys=('X_RPM_BUILD',), value='{key}\n{value}\n\n', default='%build\n\n', required=True),
    dict(key='%install', extra_keys=('X_RPM_INSTALL',), value='{key}\n{value}\n\n',
         default='%install\nmkdir -p %{{buildroot}}\ncp -a * %{{buildroot}}\n\n', required=True),
    dict(key='%files', default=file_section_wrapper, required=True, lookup=False),
    # optional
    dict(key='%clean', extra_keys=('X_RPM_CLEAN',), value='{key}\n{value}\n\n'),
    dict(key='%changelog', value='{key}\n{value}\n\n'),
    dict(key='%pre', value='{key}\n{value}\n\n'),
    dict(key='%post', value='{key}\n{value}\n\n'),
    dict(key='%preun', value='{key}\n{value}\n\n'),
    dict(key='%postun', value='{key}\n{value}\n\n'),
    dict(key='%pretrans', value='{key}\n{value}\n\n'),
    dict(key='%posttrans', value='{key}\n{value}\n\n'),
    dict(key='%verify', value='{key}\n{value}\n\n'),
]


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
            # this is a file node
            # check if this node should be prefix with a special value
            # if so we need to remove the normal PACKAGE prefix and replace it with the custom prefix
            # imple details... This logic is mapped with the rpm_package code that generates the
            # tar file that is created for the rpm build. It cached the resolved value on the node
            # we want to make sure the orginial uncached value is what is stored in the spec file
            if env.hasMetaTag(node, "RPM_NODE_PREFIX_CACHED"):
                node_prefix = env.MetaTagValue(node, "RPM_NODE_PREFIX_CACHED")
                # remove any special value we might have as ${NAME} that might exists
                rpm_prefix = env.subst(env.MetaTagValue(node, "RPM_NODE_PREFIX"))
                tmp = tmp.replace(node_prefix, rpm_prefix)
            dir_tmp = '%dir {0}'.format(os.path.split(tmp)[0])
            directories.add(dir_tmp)
            if env.hasMetaTag(node, 'POSIX_ATTR') or env.hasMetaTag(node, 'POSIX_USER') or env.hasMetaTag(node, 'POSIX_GROUP'):
                attr = env.MetaTagValue(node, 'POSIX_ATTR', default="-")
                user = env.MetaTagValue(node, 'POSIX_USER', default="-")
                group = env.MetaTagValue(node, 'POSIX_GROUP', default="-")
                tmp = '%attr({attr},{user},{group}) {node}'.format(attr=attr, user=user, group=group, node=tmp)
            files.append(tmp)
        else:
            # this is directory node
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
    # list of custom vars to add
    # these value ideally will be stuff like
    # add custom vars or advance setting that might
    # not normally be used.
    rpm_vals = env.get('RPM_VARS', [])

    # fill in the values if we have any
    if not rpm_vals:
        api.output.verbose_msg(['rpm-spec'], "No custom RPM spec variables added")
    else:
        new_vals = []
        for v in rpm_vals:
            try:
                new_vals.append(env.subst(v))
            except BaseException:
                api.output.warning_msgf("Failed to subst() value:\n {0}\n passing orginal value instead.", v)
                new_vals.append(v)
        rpm_vals = new_vals

    # open spec file
    if len(source) and source[0].name.endswith(".spec"):
        with open(source[0].abspath, 'r') as file_obj:
            file_contents = file_obj.read().split('\n')
        outstr = process_existing_spec(env, file_contents, rpm_vals)
    else:
        outstr = generate_spec(env, rpm_vals)

    with open(target[0].abspath, 'wb') as out_file:
        out_file.write(outstr.encode())

 # util function


def add_if(env, tmpl, keylst, value_mapper, default, required, lookup):
    key = keylst[0]
    if lookup:
        for i in keylst:
            if i.startswith("%"):
                i = i[1:]
            if i.lower() in env and not callable(env[i.lower()]) and env[i.lower()]:
                value = value_mapper(env, key, env[i.lower()])
                value = env.subst(value)
                return tmpl.format(
                    key=key,
                    value=value,
                )
            elif i.upper() in env and not callable(env[i.upper()]) and env[i.upper()]:
                value = value_mapper(env, key, env[i.upper()])
                value = env.subst(value)
                return tmpl.format(
                    key=key,
                    value=value,
                )

    # the value was not defined in the environment
    # do we have a default value to put in
    if not default and required:
        # no default and
        api.output.error_msgf("Value for '{}' was not defined for rpm specfile", key, stackframe=env['_parts_user_stack'])
    elif not default:
        return ""
    # we have a default
    # is it callable

    if callable(default):
        return default(env, key)
    # assume it is a string and subst() it
    return env.subst(default.format(key=keylst[0]))


def generate_values(items, env):
    out_str = ''
    for item in items:
        keys = (item['key'],) + item.get('extra_keys', ())
        tmp = add_if(
            env,
            item.get('value'),
            keys,
            item.get("value_mapper", lambda env, key, value: value),
            item.get("default", ''),
            item.get("required", False),
            item.get("lookup", True)
        )
        if tmp:
            api.output.verbose_msg(['rpm-spec'], "Adding value:\n", tmp[:-1])
            out_str += tmp

    return out_str


def generate_spec(env, rpm_vals):
    '''
    This function should become the "default" path as this generates
    the expected output for the spec file based on what is built and being installed
    '''

    out_str = ''
    if rpm_vals:
        out_str = "\n".join(rpm_vals) + "\n"

    # output headers
    out_str += generate_values(headers, env)

    # output sections
    out_str += generate_values(sections, env)

    return out_str


def process_existing_spec(env, file_contents, rpm_vals):
    '''
    This function has to modify an existing spec file
    We mostly care about in this case that we add the file list
    and required headers values we need to have to allow the build to
    work correctly. We want to in general do not touch or change anything.

    Known issue would be not handling sections well... ideally we want to move away from this
    The best way to handle this case is to not overide sections in the spec file when calling
    RpmPackage and let this code add only required stuff or missing items
    '''
    headers_not_found = headers[:]
    sections_not_found = sections[:]
    required_headers_not_found = [i['key'] for i in filter(lambda x: x.get("required"), headers)]
    required_sections_not_found = [i['key'] for i in filter(lambda x: x.get("required"), sections)]

    # this is the last known header value.. we add after this
    header_indx = 0
    file_section_idx = -1
    # find out what we have
    # add replace anything we have defined
    for idx, line in enumerate(file_contents):

        ####################################
        # if this is a headers item

        # If BuildArch exists in specfile, delete the line
        # It will take host architecture as the build architecture by default
        if line.startswith('BuildArch'):
            file_contents[idx] = '# ' + file_contents[idx]

        for item in headers:
            if line.startswith(("Source1", "Source2", "Source3", "Source4", "Source5", "Source6", "Source7", "Source8", "Source9")):
                continue

            if line.startswith(item['key']):
                # update line
                header_indx = idx
                keys = (item['key'],) + item.get("extra_keys", ())
                # do we have an override for this value
                tmp = add_if(
                    env,
                    item['value'],
                    keys,
                    item.get("value_mapper", lambda env, key, value: value),
                    item.get("default", ''),
                    # has to be False as we are modifing a file
                    # and we don't know yet if it exists until
                    # everything is read in
                    False,
                    item.get("lookup", True)
                )

                # replace value if we have something to replace with
                if tmp:
                    file_contents[idx] = tmp.strip()  # remove ending \n

                # remove header from not found list as we clearly found it
                headers_not_found = list(filter(lambda x: x['key'] != item['key'], headers_not_found))

                # check to see if this was required.. if so remove it from the list
                if item.get('required') and item['key'] in required_headers_not_found:
                    required_headers_not_found.remove(item['key'])

        for item in sections:
            if line.startswith(item['key']):
                # special case %files as we have to fill this in
                if item['key'] == '%files':
                    file_section_idx = idx
                    continue
                # if we have a section defined leave it as is just note that it happened
                sections_not_found = list(filter(lambda x: x['key'] != item['key'], sections_not_found))
                if item.get('required') and item['key'] in required_sections_not_found:
                    required_sections_not_found.remove(item['key'])

    # check for missing headers items that we can set
    for item in headers_not_found:
        keys = (item['key'],) + item.get("extra_keys", ())
        tmp = add_if(
            env,
            item['value'],
            keys,
            item.get("value_mapper", lambda env, key, value: value),
            item.get("default", ''),
            item.get("required", False),
            item.get("lookup", True)
        )
        if tmp:
            file_contents.insert(header_indx, tmp.strip())
        if item.get('required') and item['key'] in required_headers_not_found:
            required_headers_not_found.remove(item['key'])

    # something is missing error out
    if required_headers_not_found:
        api.output.error_msg("Did not find headers value(s) in spec file for {0}".format(
            ", ".join(required_headers_not_found)), show_stack=False)

    # check for missing sections and add anything we can
    # deal with the section
    # check for missing headers items that we can set
    for item in sections_not_found:
        # special case %files as we have to fill this in
        if item['key'] == '%files':
            pkg_files = env['PKG_FILES']
            prefix = add_if(
                env,
                "{value}",
                ('Prefix', 'X_RPM_PREFIX', 'PACKAGE_ROOT'),
                lambda env, key, value: value,
                None,
                True,
                True
            )
            add_files_content(env, file_contents, pkg_files, prefix, file_section_idx)
            if item.get('required') and item['key'] in required_sections_not_found:
                required_sections_not_found.remove(item['key'])

        else:
            keys = (item['key'],) + item.get("extra_keys", ())
            tmp = add_if(
                env,
                item['value'],
                keys,
                item.get("value_mapper", lambda env, key, value: value),
                item.get("default", ''),
                item.get("required", False),
                item.get("lookup", True)
            )
            if tmp:
                file_contents.append(tmp)
            if item.get('required') and item['key'] in required_sections_not_found:
                required_sections_not_found.remove(item['key'])

    # something is missing error out
    if required_sections_not_found:
        api.output.error_msg("Did not find section(s) in spec file for {0}".format(
            ", ".join(required_sections_not_found)), show_stack=False)

    if rpm_vals:
        file_contents = rpm_vals + file_contents

    file_contents = "\n".join(file_contents) + '\n'

    return file_contents


rpmspec_action = SCons.Action.Action(rpm_spec)

api.register.add_builder('_rpmspec', SCons.Builder.Builder(
    action=rpmspec_action,
    source_factory=SCons.Node.FS.File,
    target_factory=SCons.Node.FS.File,
))
