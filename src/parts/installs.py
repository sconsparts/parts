

import json
import os

import SCons.Script
import SCons.Tool.install
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

import parts.api as api
import parts.common as common
import parts.core.scanners as scanners
import parts.core.util as util
import parts.errors as errors
import parts.exportitem as exportitem
import parts.glb as glb
import parts.pattern as pattern
import parts.platform_info as platform_info
import parts.sdk as sdk

# need better configuration control
# these function will hopfully be replaced later once a better solution shows it self

g_installargs = {}


def SetDefaultInstallArguments(category, **kw):
    '''
    Sets up flags that will automatically be added to a given catgory of Install
    This is more of hack, then a proper solution
    '''
    try:
        g_installargs[category].update(kw)
    except KeyError:
        g_installargs[category] = kw


def get_args(cat, **kw):

    args = {}
    tmp = g_installargs.get(cat, {})
    args.update(tmp)
    args.update(kw)
    try:
        args['tags']['category'] = cat
    except Exception:
        args['tags'] = {'category': cat}
    return args

#############################


def ProcessInstall(env, target, sources, sub_dir, create_sdk, sdk_dir='', no_pkg=False, **kw):

    # list of file we installed (dest)
    installed_files = []
    # list of all files we install (source, or where we installed from)
    src_lst = []
    # dictionary of MetaTag we want to add to any file we installed
    tags = {}

    target = env.subst(target)
    target_lib = env.subst('${INSTALL_LIB}')
    target_include = env.subst('${INSTALL_INCLUDE}')
    pkg_config = env.subst('${INSTALL_PKG_CONFIG}')

    if sub_dir != '' and sdk_dir != '':
        dest_dir = os.path.join(target, sub_dir)
        pattern_dest_sdk = os.path.join(sdk_dir, sub_dir)
    elif sub_dir != '':
        dest_dir = os.path.join(target, sub_dir)
        pattern_dest_sdk = sdk_dir
    else:
        dest_dir = target
        pattern_dest_sdk = sdk_dir
    dest_dir = env.Dir(dest_dir)
    pattern_dest_sdk = env.Dir(pattern_dest_sdk)

    dest_sdk = sdk_dir

    if 'tags' in kw:
        tags = kw['tags']
        del kw['tags']
    if no_pkg == True:
        tags['no_package'] = True

    def do_sdk(sources):
        if target == target_lib:
            ret = env.SdkItem(
                '$SDK_LIB', [sources], sub_dir, '', [
                    (exportitem.EXPORT_TYPES.FILE, 'LIBS'),
                    (exportitem.EXPORT_TYPES.PATH, 'LIBPATH'),
                    (exportitem.EXPORT_TYPES.PATH, 'RPATHLINK')
                ],
                add_to_path=kw.get(
                    'add_to_path', True), auto_add_file=kw.get(
                    'auto_add_libs', True), use_build_dir=True, create_sdk=create_sdk
            )
        elif target == target_include:
            ret = env.SdkItem('$SDK_INCLUDE', [sources], sub_dir, '', [(exportitem.EXPORT_TYPES.PATH, 'CPPPATH')],
                              add_to_path=kw.get('add_to_path', None),
                              auto_add_file=True,
                              use_src_dir=kw.get('use_src_dir', False),
                              use_build_dir=False,
                              create_sdk=create_sdk
                              )
        elif target == pkg_config:
            ret = env.SdkItem('$SDK_PKG_CONFIG', [sources], sub_dir, '', [(exportitem.EXPORT_TYPES.PATH, 'PKG_CONFIG_PATH')],
                              create_sdk=create_sdk)
        else:
            ret = env.SdkItem(dest_sdk, [sources], sub_dir, '', [],
                              create_sdk=create_sdk,
                              add_to_path=kw.get('add_to_path', True),
                              auto_add_file=kw.get('auto_add_file', True)
                              )

        return ret

    if sdk_dir != '':
        for s in sources:
            if isinstance(s, pattern.Pattern):
                # this case with pattern is not ideal at the moment
                # there is a case in which a file may be new, causing a re-addition of the files in the
                # export table.
                sdk_files = s.target_source(pattern_dest_sdk)[0]
                # do we even have something in the pattern?
                if sdk_files:
                    missingsdk = False if sdk.g_sdked_files else True
                    ret = None
                    # if so see if we need to SDK it
                    for sdkfile in s.target_source(pattern_dest_sdk)[0]:
                        if sdkfile not in sdk.g_sdked_files:
                            missingsdk = True
                            break
                    # did we find something to SDK?
                    if missingsdk:
                        ret = do_sdk(s)

                    sdkf, sr = s.target_source(pattern_dest_sdk)
                    inst, sr = s.target_source(dest_dir)
                    # translate the pattern to the install form correctly
                    inc = []
                    pdir = env.subst(sdk_dir)
                    l = len(pdir)
                    for i in sdkf:
                        inc.append(env.File(i).path[l:])
                    # src_lst is what is returned to make sure the auto generated SDK work latter.
                    # we can use the pattern here for the Install call as the files don't exist in the
                    # sdk area during the first run.
                    src_lst.append(pattern.Pattern(src_dir=pdir, includes=inc, recursive=s.recursive))
                    # take sdk pattrens outputs (targets) as the source and use the same pattern
                    # assuming it would copy to the Install area, outputs as the targets
                    installed_files.extend(env.InstallAs(inst, sdkf, tags=tags, **kw))

            elif isinstance(s, SCons.Node.FS.Dir):
                if s not in sdk.g_sdked_files:
                    ret = do_sdk(s)
                else:
                    ret = [s]
                out = env.Install(dest_dir, ret, tags=tags, **kw)
                installed_files.extend(out)
                src_lst.append(env.Dir(ret[0]))
            elif isinstance(s, SCons.Node.FS.File):
                if s not in sdk.g_sdked_files:
                    ret = do_sdk(s)
                else:
                    ret = [s]

                installed_files.extend(env.Install(dest_dir, ret, tags=tags, **kw))
                if util.isString(ret[0]):
                    ret[0] = env.File(ret[0])
                src_lst.append(ret[0])
            elif isinstance(s, SCons.Node.Node) or util.isString(s):
                if s not in sdk.g_sdked_files:
                    ret = do_sdk(s)
                else:
                    ret = [s]

                installed_files.extend(env.Install(dest_dir, ret, tags=tags, **kw))
                src_lst.append(env.Entry(ret[0]))
            else:
                api.output.warning_msg("Unknown type {} in ProcessInstall() in installs.py".format(type(s)))

    else:

        for s in sources:
            if isinstance(s, pattern.Pattern):
                t, sr = s.target_source(dest_dir)
                if t:
                    installed_files += env.InstallAs(t, sr, tags=tags, **kw)
                    src_lst.append(s)
            elif isinstance(s, SCons.Node.FS.Dir):
                out = env.Install(dest_dir, s, tags=tags, **kw)
                installed_files += out
                src_lst.append(env.Dir(s))
            else:
                installed_files += env.Install(dest_dir, s, tags=tags, **kw)
                src_lst.append(env.File(s))

    return installed_files, src_lst


def json_manifest_builder(target, source, env):
    l = len("Value:")
    with open(target[0].get_path(), 'w') as outfile:
        data = json.dumps([i.ID[l:] for i in source], indent=2,)
        outfile.write(data)


api.register.add_builder('_InstallManifest', SCons.Builder.Builder(
    action=SCons.Action.Action(json_manifest_builder, "Writing manifest out files to be installed"),
    target_factory=SCons.Node.FS.File,
    source_factory=SCons.Node.Python.Value,
    source_scanner=scanners.NullScanner,
    target_scanner=scanners.NullScanner,
    multi=True
))


def InstallItem(env, target, source, sub_dir="", sdk_dir='', no_pkg=False, create_sdk=True, **kw):
    '''Actually install source files into target location within product
    packaging, and tag with the Part's alias so we know where it came from.

    env         -- the Environment for the Part being processed
    source      -- the file(s) to be installed; can be a single file, a list of
                   files, or a Pattern result
    target      -- the place within the product package to hold source
    returns     -- the return value of the Install call, so that callers can
                   subsequently further MetaTag these files'''
    errors.SetPartStackFrameInfo(True)
    if env['CREATE_SDK'] == False and create_sdk == True:
        create_sdk = False
    source = common.make_list(source)

    pobj = glb.engine._part_manager._from_env(env)
    # this is for classic formats and compatible behavior with 0.9
    pobj._sdk_or_installed_called = True

    installed_files, src_files = ProcessInstall(env, target, source, sub_dir, create_sdk, sdk_dir, no_pkg, **kw)
    file_values = [env.Value("Value:{}".format(i.ID)) for i in installed_files if i not in pobj.DefiningSection.InstalledFiles]
    if file_values:
        is_part_dyn = env.get("_PARTS_DYN", kw.get("_PARTS_DYN"))
        # this defines some state file with what will be generated. These files only contain state, not direct file
        # node relationships ( this is why they are Value nodes )
        install_state_name = "${{PARTS_SYS_DIR}}/${{PART_ALIAS}}.${{PART_SECTION}}.install.{type}.{cat}.jsn".format(
            cat=target[1:], type="dyn" if is_part_dyn else "emit")
        manifest = env._InstallManifest(install_state_name, file_values)

        env._map_dyn_export_(manifest) if is_part_dyn else env._map_export_(manifest)

        if is_part_dyn:
            # This maps the data to the section of this part.
            section = pobj.Section(env["PART_SECTION"])
            section._map_target(installed_files, target[1:].replace("_", ""))

        # add installed file to Part object
        pobj.DefiningSection.InstalledFiles.update(installed_files)

        env.MetaTag(
            installed_files, 'package',
            part_alias=env['ALIAS'],
            part_name=env.subst('$PART_NAME'),
            part_version=env.subst('$PART_VERSION')
        )

    errors.ResetPartStackFrameInfo()
    return installed_files


# Do we need to CLEAN these directories??

def InstallTarget(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):
    '''Put files into the "executable" area within the product packaging.

    env         -- the Environment for the Part being processed
    source   -- the file(s) to be installed; can be a single file, a list of
                   files, or a Pattern result
    sub_dir     -- the optional directory structure to impose'''

    # Look at the Node and its builder and then based on the type of builder
    # we know what kind of thing it is. That's the future direction.

    errors.SetPartStackFrameInfo(True)
    if util.isList(source) == False:
        source = [source]
    source = SCons.Script.Flatten(source)

    installed_files = []

    for i in source:
        # We have an individual item
        if isinstance(i, SCons.Node.FS.File) or isinstance(
                i, SCons.Node.FS.Dir) or isinstance(i, SCons.Node.Node) or util.isString(i):

            if i not in sdk.g_sdked_files:
                ret = env.SdkTarget([i], sub_dir)
            else:
                ret = [i]

            if common.is_category_file(env, 'INSTALL_LIB_PATTERN', i):
                top_dir = '$INSTALL_LIB'
                category = 'LIB'
                expottype = 'INSTALLLIB'

            elif common.is_category_file(env, 'INSTALL_BIN_PATTERN', i):
                top_dir = '$INSTALL_BIN'
                category = 'BIN'
                expottype = 'INSTALLBIN'

            else:
                continue
            itmp = InstallItem(env, top_dir, ret, sub_dir,
                               no_pkg=no_pkg, create_sdk=create_sdk, **get_args(category, **kw))

            installed_files += itmp
        elif isinstance(i, pattern.Pattern):
            # we have a pattern item

            for td in i.sub_dirs():
                if td != '':
                    new_sub_dir = os.path.join(str(sub_dir), str(td))
                else:
                    new_sub_dir = sub_dir

                for d in i.files(td):
                    if d not in sdk.g_sdked_files:
                        ret = env.SdkTarget([d], sub_dir)
                    else:
                        ret = [d]
                    if common.is_category_file(env, 'INSTALL_LIB_PATTERN', d):
                        top_dir = '$INSTALL_LIB'
                        itmp = InstallItem(env, top_dir, ret, new_sub_dir,
                                           no_pkg=no_pkg, create_sdk=create_sdk, **get_args('LIB', **kw))

                        installed_files += itmp

                    elif common.is_category_file(env, 'INSTALL_BIN_PATTERN', d):
                        top_dir = '$INSTALL_BIN'
                        itmp = InstallItem(env, top_dir, ret, new_sub_dir,
                                           no_pkg=no_pkg, create_sdk=create_sdk, **get_args('BIN', **kw))

                        installed_files += itmp

                    else:
                        pass
        # Unless is_bin_file gets smarter, this will be a problem on Linux
        # since there are no executable extensions there!

        else:
            # print 'Told to InstallTarget', i, '...what should I do?'
            continue

    errors.ResetPartStackFrameInfo()
    return installed_files


def InstallTools(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_TOOLS', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_TOOLS', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('TOOLS', **kw))

    return installed_files


def InstallAPI(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_API', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_API', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('API', **kw))

    return installed_files


def InstallLib(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_LIB', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_LIB', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('LIB', **kw))

    return installed_files


def InstallBin(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_BIN', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_BIN', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('BIN', **kw))

    return installed_files


def InstallSystemBin(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_SYSTEM_BIN', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_SYSTEM_BIN', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('SYSTEM_BIN', **kw))

    return installed_files


def InstallPrivateBin(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_PRIVATE_BIN', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_PRIVATE_BIN', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('PRIVATE_BIN', **kw))

    return installed_files


def InstallConfig(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_CONFIG', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_CONFIG', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('CONFIG', **kw))

    return installed_files


def InstallDoc(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_DOC', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_DOC', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('DOC', **kw))

    return installed_files


def InstallHelp(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_HELP', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_HELP', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('HELP', **kw))

    return installed_files


def InstallManPage(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_MANPAGE', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_MANPAGE', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('MANPAGE', **kw))

    return installed_files


def InstallMessage(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_MESSAGE', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_MESSAGE', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('MESSAGE', **kw))

    return installed_files


def InstallPkgConfig(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_PKG_CONFIG', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_PKG_CONFIG', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('PKG_CONFIG', **kw))

    return installed_files


def InstallResource(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_RESOURCE', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_RESOURCE', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('RESOURCE', **kw))

    return installed_files


def InstallSample(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_SAMPLE', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_SAMPLE', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('SAMPLE', **kw))

    return installed_files


def InstallData(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_DATA', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_DATA', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('DATA', **kw))

    return installed_files


def InstallSource(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_SOURCE', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_SOURCE', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('SOURCE', **kw))

    return installed_files


def InstallInclude(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_INCLUDE', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_INCLUDE', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('INCLUDE', **kw))

    return installed_files


def InstallTopLevel(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_TOP_LEVEL', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_TOP_LEVEL', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('TOP_LEVEL', **kw))

    return installed_files


def PkgNoInstall(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$PKG_NO_INSTALL', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_NO_PKG', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('NO_INSTALL', **kw))

    return installed_files


def InstallPython(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_PYTHON', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_PYTHON', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('PYTHON', **kw))

    return installed_files


def InstallScript(env, source, sub_dir='', no_pkg=False, create_sdk=True, **kw):

    installed_files = InstallItem(env, '$INSTALL_SCRIPT', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_SCRIPT', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('SCRIPT', **kw))

    return installed_files


def InstallPkgData(env, source, sub_dir='', no_pkg=False, create_sdk=True, packagetype=None, **kw):
    # this function is used to install control files for different packages.
    # packagetype is to specify what is the package type. For example if packagetype = 'dpkg',
    # will associate control file installed using this function for debian type only.
    # input given by user for packegetype should be in lowercase.

    installed_files = InstallItem(env, '$INSTALL_PKGDATA', source,
                                  sub_dir=sub_dir, sdk_dir='$SDK_PKGDATA', no_pkg=no_pkg, create_sdk=create_sdk,
                                  **get_args('PKGDATA', **kw))

    # Normalizing packagetype to be in lower case and without a dot.
    # If user gives packagetype as TARGZ or TAR.GZ or tar.gz or targz
    # All the cases will be normalized to targz.

    if packagetype is not None:
        pkgtype = []
        for packagetype1 in packagetype:
            pkgtype.append(packagetype1.lower().replace('.', ''))
        packagetype = common.make_list(pkgtype)
        env.MetaTag(installed_files, 'package', types=packagetype)

    return installed_files


# adding logic to Scons Environment object
SConsEnvironment.InstallAPI = InstallAPI
SConsEnvironment.InstallBin = InstallBin
SConsEnvironment.InstallConfig = InstallConfig
SConsEnvironment.InstallData = InstallData
SConsEnvironment.InstallSource = InstallSource
SConsEnvironment.InstallDoc = InstallDoc
SConsEnvironment.InstallHelp = InstallHelp
SConsEnvironment.InstallInclude = InstallInclude
SConsEnvironment.InstallLib = InstallLib
SConsEnvironment.InstallManPage = InstallManPage
SConsEnvironment.InstallMessage = InstallMessage
SConsEnvironment.InstallPkgConfig = InstallPkgConfig
SConsEnvironment.InstallPkgData = InstallPkgData
SConsEnvironment.InstallPrivateBin = InstallPrivateBin
SConsEnvironment.InstallSystemBin = InstallSystemBin
SConsEnvironment.InstallLibExec = InstallPrivateBin
SConsEnvironment.InstallPython = InstallPython
SConsEnvironment.InstallResource = InstallResource
SConsEnvironment.InstallSample = InstallSample
SConsEnvironment.InstallScript = InstallScript
SConsEnvironment.InstallTarget = InstallTarget
SConsEnvironment.InstallTools = InstallTools
SConsEnvironment.InstallTopLevel = InstallTopLevel

SConsEnvironment.PkgNoInstall = PkgNoInstall
SConsEnvironment.InstallNoPkg = PkgNoInstall

SConsEnvironment.InstallItem = InstallItem

# add configuartion variable

api.register.add_variable('PART_INSTALL_CONCEPT', 'install${ALIAS_SEPARATOR}', '')
api.register.add_variable('INSTALL_ROOT_DIR', '#_install', '')
api.register.add_variable('INSTALL_ROOT', '${INSTALL_ROOT_DIR}/${CONFIG}_${TARGET_PLATFORM}_${TOOLCHAIN.replace(",","_")}', '')

# this might be useful
api.register.add_variable('INSTALL_RELATIVE_LIB', '${__env__.Dir(INSTALL_BIN).rel_path(__env__.Dir(INSTALL_LIB))}', '')

# location mappings mix of posix and some extras
api.register.add_variable('INSTALL_LIB_SUBDIR', 'lib', '')
api.register.add_variable('INSTALL_BIN_SUBDIR', 'bin', '')
api.register.add_variable('INSTALL_INCLUDE_SUBDIR', 'include', '')

if 'win32' == glb._host_platform:
    api.register.add_variable('INSTALL_CONFIG_SUBDIR', 'config', '')
    api.register.add_variable('INSTALL_PRIVATE_BIN_SUBDIR', 'private/bin', '')
    api.register.add_variable('INSTALL_SYSTEM_BIN_SUBDIR', 'system/bin', '')
    api.register.add_variable('INSTALL_DATA_SUBDIR', 'data', '')
    api.register.add_variable('INSTALL_DOC_SUBDIR', 'doc', '')
    api.register.add_variable('INSTALL_HELP_SUBDIR', 'help', '')
    api.register.add_variable('INSTALL_MANPAGE_SUBDIR', 'man', '')
    api.register.add_variable('INSTALL_MESSAGE_SUBDIR', 'message', '')
    api.register.add_variable('INSTALL_PKG_CONFIG_SUBDIR', 'pkgconfig', '')

else:  # assume posix like layout
    api.register.add_variable('INSTALL_CONFIG_SUBDIR', 'etc', '')
    api.register.add_variable('INSTALL_PRIVATE_BIN_SUBDIR', 'libexec', '')
    api.register.add_variable('INSTALL_SYSTEM_BIN_SUBDIR', 'sbin', '')
    api.register.add_variable('INSTALL_DATA_SUBDIR', 'share', '')
    api.register.add_variable('INSTALL_DOC_SUBDIR', 'share/doc', '')
    api.register.add_variable('INSTALL_HELP_SUBDIR', 'share/doc', '')
    api.register.add_variable('INSTALL_MANPAGE_SUBDIR', 'share/man', '')
    api.register.add_variable('INSTALL_MESSAGE_SUBDIR', 'share/nls', '')
    api.register.add_variable('INSTALL_PKG_CONFIG_SUBDIR', '${INSTALL_LIB_SUBDIR}/pkgconfig', '')

# this is not really defined in posix .. but useful
api.register.add_variable('INSTALL_SOURCE_SUBDIR', 'src', '')
api.register.add_variable('INSTALL_API_SUBDIR', 'API', '')
api.register.add_variable('INSTALL_TOOLS_SUBDIR', 'tools', '')
api.register.add_variable('INSTALL_RESOURCE_SUBDIR', 'resource', '')
api.register.add_variable('INSTALL_SAMPLE_SUBDIR', 'samples', '')
api.register.add_variable('INSTALL_TOP_LEVEL_SUBDIR', '', '')
api.register.add_variable('INSTALL_PYTHON_SUBDIR', 'python', '')
api.register.add_variable('INSTALL_SCRIPT_SUBDIR', 'scripts', '')
api.register.add_variable('INSTALL_PKGDATA_SUBDIR', 'pkgdata', '')

# stuff to have installed in local sandbox but not in package
api.register.add_variable('PKG_NO_INSTALL_SUBDIR', 'NOINSTALL', '')


# Map the install variable to the
api.register.add_variable('INSTALL_LIB', '${INSTALL_ROOT}/${INSTALL_LIB_SUBDIR}', '')
api.register.add_variable('INSTALL_BIN', '${INSTALL_ROOT}/${INSTALL_BIN_SUBDIR}', '')
api.register.add_variable('INSTALL_PRIVATE_BIN', '${INSTALL_ROOT}/${INSTALL_PRIVATE_BIN_SUBDIR}', '')
api.register.add_variable('INSTALL_SYSTEM_BIN', '${INSTALL_ROOT}/${INSTALL_SYSTEM_BIN_SUBDIR}', '')
api.register.add_variable('INSTALL_TOOLS', '${INSTALL_ROOT}/${INSTALL_TOOLS_SUBDIR}', '')
api.register.add_variable('INSTALL_API', '${INSTALL_ROOT}/${INSTALL_API_SUBDIR}', '')
api.register.add_variable('INSTALL_INCLUDE', '${INSTALL_ROOT}/${INSTALL_INCLUDE_SUBDIR}', '')
api.register.add_variable('INSTALL_CONFIG', '${INSTALL_ROOT}/${INSTALL_CONFIG_SUBDIR}', '')
api.register.add_variable('INSTALL_DOC', '${INSTALL_ROOT}/${INSTALL_DOC_SUBDIR}', '')
api.register.add_variable('INSTALL_HELP', '${INSTALL_ROOT}/${INSTALL_HELP_SUBDIR}', '')
api.register.add_variable('INSTALL_MANPAGE', '${INSTALL_ROOT}/${INSTALL_MANPAGE_SUBDIR}', '')
api.register.add_variable('INSTALL_MESSAGE', '${INSTALL_ROOT}/${INSTALL_MESSAGE_SUBDIR}', '')
api.register.add_variable('INSTALL_RESOURCE', '${INSTALL_ROOT}/${INSTALL_RESOURCE_SUBDIR}', '')
api.register.add_variable('INSTALL_SAMPLE', '${INSTALL_ROOT}/${INSTALL_SAMPLE_SUBDIR}', '')
api.register.add_variable('INSTALL_DATA', '${INSTALL_ROOT}/${INSTALL_DATA_SUBDIR}', '')
api.register.add_variable('INSTALL_SOURCE', '${INSTALL_ROOT}/${INSTALL_SOURCE_SUBDIR}', '')
api.register.add_variable('INSTALL_TOP_LEVEL', '${INSTALL_ROOT}/${INSTALL_TOP_LEVEL_SUBDIR}', '')
api.register.add_variable('PKG_NO_INSTALL', '${INSTALL_ROOT}/${INSTALL_NO_INSTALL_SUBDIR}', '')
api.register.add_variable('INSTALL_PYTHON', '${INSTALL_ROOT}/${INSTALL_PYTHON_SUBDIR}', '')
api.register.add_variable('INSTALL_SCRIPT', '${INSTALL_ROOT}/${INSTALL_SCRIPT_SUBDIR}', '')
api.register.add_variable('INSTALL_PKGDATA', '${INSTALL_ROOT}/${INSTALL_PKGDATA_SUBDIR}', '')
api.register.add_variable('INSTALL_PKG_CONFIG', '${INSTALL_ROOT}/${INSTALL_PKG_CONFIG_SUBDIR}', '')


# file patterns
api.register.add_list_variable('INSTALL_LIB_PATTERN', ['*.so', '*.sl', '*.so.*', '*.sl.*', '*.so-gz', '*.dlsym', '*.dylib'], '')
api.register.add_list_variable('INSTALL_API_LIB_PATTERN', ['*.lib', '*.a'], '')
# api.register.add_list_variable('AUTO_TAG_INSTALL',[('*.pdb',{'no_package':True})],'')
api.register.add_bool_variable('AUTO_TAG_ON_INSTALL', True, '')

if 'win32' == glb._host_platform:
    api.register.add_list_variable('INSTALL_BIN_PATTERN', ['*.dll', '*.DLL',
                                                           '*.exe', '*.EXE', '*.com', '*.COM', '*.pdb', '*.PDB'], '')
else:
    api.register.add_list_variable('INSTALL_BIN_PATTERN', ['*'], '')


api.register.add_global_object('SetDefaultInstallArguments', SetDefaultInstallArguments)

# vim: set et ts=4 sw=4 ai ft=python :
