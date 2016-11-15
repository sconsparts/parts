'''
Defines a builder for .deb packages
'''
import re

import SCons.Action
import SCons.Builder
import SCons.Defaults
import SCons.Node.FS
import SCons.Node.Python
import SCons.Script

import parts.api as api
import parts.packaging as packaging

from parts.errors import GetPartStackFrameInfo, ResetPartStackFrameInfo, SetPartStackFrameInfo

DEB_REG = r"(\w+)\_([\d.]+)(\-([\w.]+))?\_(\w+)\.deb"


def dep_target_scanner(node, env, _):
    '''
    Scanner function for dbpkg builder
    '''
    groups = env.MetaTagValue(node, 'groups', 'dpkg', default=[]) or packaging.PackageGroups()
    files, _ = env.GetFilesFromPackageGroups(
        node, groups,
        stackframe=env.MetaTagValue(node, 'stackframe', 'bpkg', default=None))
    tar_gz_entries = []
    debian_entries = []
    pack_dir = node.attributes.pack_dir
    for entry in files:
        if (env.MetaTagValue(entry, 'category', 'package') == 'PKGDATA' and
                'dpkg' in env.MetaTagValue(entry, 'type', 'package', ['dpkg', 'deb', 'DEB'])):
            new_entry = pack_dir.Dir('debian').Entry(entry.name)
            if not new_entry.has_builder():
                env.CCopyAs(new_entry, entry, CCOPY_LOGIC='hard-soft')
            debian_entries.append(new_entry)
        else:
            tar_gz_entries.append(entry)
    node.attributes.tar_gz = tar_gz = pack_dir.Entry(node.attributes.pack_name + '.tar.gz')
    if not tar_gz.has_builder():
        env.TarGzFile(tar_gz, tar_gz_entries, SRC_DIR='$INSTALL_ROOT')
    node.attributes.files_to_pack = tar_gz_entries
    return tar_gz_entries + debian_entries + [tar_gz]

def dep_emitter(target, source, env):
    '''
    Dpkg builder emitter function
    '''
    target = env.arg2nodes(target, env.fs.File)
    grps = re.match(DEB_REG, target[0].name, re.IGNORECASE)
    if grps is None:
        api.output.error_msg(
            ("DEB target files must be in format of <name>_<version>-<release>_<arch>.deb "
             "or <name>_<version>_<arch>.deb\n "
             "current format of value of target file is '{0}'").format(target[0].name))
    target_name, target_version, _, _, _ = grps.groups()
    node = target[0]
    node.attributes.target_name = target_name
    node.attributes.pack_name = pack_name = target_name + '_' + target_version
    node.attributes.pack_dir = env.Dir('${BUILD_DIR}/_dpkg/' + pack_name)
    source = [env.subst(str(s)) for s in source]

    SetPartStackFrameInfo()
    env.MetaTag(target, 'dpkg', groups=source, stackframe=GetPartStackFrameInfo())
    ResetPartStackFrameInfo()

    return target, source

def dep_create_install_file(target, source, env):
    '''
    Action to create debian/<package>.install file.
    The file should content file names to be installed and
    directories where to put them on a target machine
    '''
    pack_dir = target[0].attributes.pack_dir
    install_file = pack_dir.File(
        'debian/' + target[0].attributes.target_name + '.install')
    file_name = install_file.abspath
    install_root = env.Dir('$INSTALL_ROOT')
    with open(file_name, 'w') as install_file:
        install_file.write('\n'.join(
            ' '.join((pack_dir.rel_path(x), 'usr/' + install_root.rel_path(x.dir)))
            for x in target[0].attributes.files_to_pack))
    return None

api.register.add_builder(
    'DPKGPackage',
    SCons.Builder.Builder(
        action=SCons.Action.Action([
            SCons.Action.Action(dep_create_install_file),
            'cd ${TARGET.attributes.pack_dir}; debuild -us -uc -d -b; cd -',
            SCons.Defaults. Copy('$TARGET', '${TARGET.attributes.pack_dir}/../${TARGET.name}')
            ], cmdstr='Packing into ${TARGET}'),
        emitter=dep_emitter,
        suffix='.deb',
        ensure_suffix=True,
        target_scanner=SCons.Script.Scanner(dep_target_scanner),
        target_factory=SCons.Node.FS.Entry,
        source_factory=SCons.Node.Python.Value
    )
)

# vim: set et ts=4 sw=4 ai :

