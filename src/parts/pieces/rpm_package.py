from __future__ import absolute_import, division, print_function

import operator
import os
import platform
import re
import json
import shutil
import subprocess
from builtins import filter

import parts.api as api
import parts.common as common
import parts.errors as errors
import parts.node_helpers as node_helpers
import parts.platform_info as platform_info
import parts.glb as glb
import SCons.Script
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

rpm_reg = r"([\w_.-]+)-([\w.]+)-([\w_.]+)[.](\w+)\.rpm"


def rpm_scan_check(node, env):
    api.output.verbose_msgf(["rpm-scanner", "scanner"], "Scanner Check {} - started", node.ID)
    # we can scan given the children all all built or up to date
    ret = not node_helpers.has_children_changed(node)
    api.output.verbose_msgf(["rpm-scanner", "scanner"], "Scanner Check {}: {}", node.ID, ret)
    return ret


def rpm_group_values(env, dir, target, source, arg=None):
    '''
    This functions returns the file that are part
    of a given package group
    '''
    api.output.verbose_msgf(["rpm-scanner", "scanner"], "Path finder - Getting source file")
    ret = []
    for node in source:
        if os.path.exists(node.ID):
            with open(node.ID, "r") as infile:
                data = json.load(infile)
                ret += [env.Entry(d) for d in data]
    api.output.verbose_msgf(["rpm-scanner", "scanner"], "Path finder - Source file= {}",
                            common.DelayVariable(lambda: [r.ID for r in ret]))
    return tuple(ret)

g_cache = {}
def rpm_scanner(node, env, path, args=None):
    '''
    The goal of the scanner is to add the depend of the rpm
    the .spec file and the .tar.gz file that we need generate
    from the sources that are mapped to a given group
    '''
    api.output.verbose_msgf(["rpm-scanner", "scanner", "scanner-called"], "Rpm Scanning {}", node.ID)

    # this is the package name without the .rpm"
    base_name = node.name[:-4]

    # get the file that are part of the package groups
    [e.disambiguate() for e in path]

    if not path:
        api.output.verbose_msgf(["rpm-scanner", "scanner"], "no sources defined yet for {}", node.ID)
        return []
    api.output.verbose_msgf(["rpm-scanner", "scanner"], "Source files: {}", common.DelayVariable(lambda: [e.ID for e in path]))

    ret = g_cache.get(node.ID)

    if not ret:
        #############################################
        # Sort files in to source group and to control group
        spec_in = []

        def spec(node):
            if env.MetaTagValue(node, 'category', 'package') == 'PKGDATA':
                if 'rpm' in env.MetaTagValue(node, 'types', 'package', ['rpm']):
                    if node.ID.endswith(".spec"):
                        spec_in.append(node)
                    else:
                        env.CCopy('${{BUILD_DIR}}/SPECS/{0}'.format(base_name), node)
                return False
            return True

        # after this call spec_in should contain the spec file
        # src should be all the sources we want to add to the .tar.gz
        src = list(filter(spec, path))

        # get various data based on the rpm name
        grps = re.match(rpm_reg, node.name, re.IGNORECASE)
        target_name = grps.group(1)
        target_version = grps.group(2)
        target_release = grps.group(3)
        target_arch = grps.group(4)

        # make sure the TARGET_ARCH matched the value in the RPM file
        # we set the value to ensure it subst correctly
        env['TARGET_ARCH'] = target_arch
        filename = target_name + '-' + target_version

        #######################################################
        # Generate the tar.gz file
        #######################################################

        #######################################################
        # iterate the src list to tweak paths and any meta values we need to tweak

        pkg_nodes = []
        env['RPM_BUILD_ROOT'] = "${{BUILD_DIR}}/{0}".format(filename)
        filtered_src = []

        v1=env.get('allow_duplicates')
        v2=env.get('_PARTS_DYN')
        env['allow_duplicates']=True
        env['_PARTS_DYN']=True

        for n in src:

            # get catagory of this node
            pk_type = env.MetaTagValue(n, 'category', 'package')

            ###############################################################
            # Process the package filters. These allow us to call other build
            # action to process items, such as runpath tweaking or tweaking
            # config files such as pkgcfg (.pc) files to have the prefix
            # to path where the file will be installed.

            preaction_filters = env.get("modify_callbacks", [])
            filtered = n

            for pfilter in preaction_filters:
                api.output.trace_msgf(["rpm-scanner-filter","rpm-scanner", "scanner"], "Applying filter to {}", filtered.ID)
                filtered_node = pfilter(filtered, env)
                if filtered_node:
                    filtered = filtered_node

            # check to see if this type of file should be have the runpath
            if pk_type in ("BIN", "LIB", "PRIVATE_BIN"):
                # we call build to modify the runpath as needed
                # depending on what PACKAGE_RUNPATH is set to
                # may remove , do nothing or change the runpath of a binary
                # This build should also check if it is a binary and skip
                # "scripts" or text files that make be installed in these areas
                filtered = env.SetRPath(filtered, RPATH_TARGET_PREFIX="$BUILD_DIR/_RPM_RUNPATH_${PART_MINI_SIG}", allow_duplicates=True)
                filtered_src += filtered
            else:
                filtered_src.append(filtered)

            # check if this node has special prefix value we want to
            # map to ( add more notes here on this logic)
            if env.hasMetaTag(n, "RPM_NODE_PREFIX"):
                prefix_value = env.MetaTagValue(n, "RPM_NODE_PREFIX")
                # call rpm to get the value this would map to
                try:
                    pkg_dir = subprocess.check_output(["rpm", "--eval", prefix_value]).strip().decode()
                    # set value on node to avoid looking this up again later
                    env.MetaTag(n, RPM_NODE_PREFIX_CACHED=pkg_dir)
                except BaseException:
                    api.output.error_msg("rpm was not found")
            else:
                pkg_dir = "${{PACKAGE_{0}}}".format(pk_type)

            # This maps the node to the "package" location based on where it was installed it
            # the details that have to looked at are that the INSTALL_XXX directory maybe different
            # for any given node as they can come from different Parts. This is why we refer to the node
            # env object to get the correct value if the INSTALL_XXX directory. The important detail is that
            # the location the exists in subdirectory of some sort. We have to ensure that subdirectory is
            # not lost when mapped to the finial package location.
            tmp_node = env.Entry(
                '${{BUILD_DIR}}/{0}/{1}/{2}'.format(
                    filename,
                    pkg_dir,
                    n.env.Dir(n.env['INSTALL_{0}'.format(pk_type)]).rel_path(n)
                )
            )
            # check that a node is not defined more than one ( could , but should not happen with overlapping package groups)
            if tmp_node in pkg_nodes:
                api.output.error_msg("Node: {0} was defined twice for package {1}".format(n, node.name), show_stack=False)
            # add to the node we want to package up in the tar.gz file
            pkg_nodes.append(tmp_node)

        env['allow_duplicates']=v1
        env['_PARTS_DYN']=v2

        # copy nodes to location for creating the tar.gz file in the structure of the finial install
        ret = env.CCopyAs(pkg_nodes, filtered_src, CCOPY_LOGIC='hard-copy', allow_duplicates=True)

        # create the tar.gz file
        # archive the source file to be added to RPM needs to be in form of <target_name>-<target_version>.tar.gz
        overrides = env.overrides.copy()
        #overrides.update(
            #allow_duplicates=True
        #)

        tar_file = [env.File('${{BUILD_DIR}}/_rpm/{0}/SOURCES/{1}.tar.gz'.format(base_name, filename))]

        #if not tar_file[0].isBuilt:
        api.output.verbose_msgf(["rpm-scanner", "scanner"], "Calling RPM Tar file generator")
        tar_file = env.TarGzFile(
            tar_file,
            ret,
            **overrides
        )
        #else:
            #api.output.verbose_msgf(["rpm-scanner", "scanner"], "RPM Tar file generator BUILT",tar_file.ID)

        # define the spec file
        overrides = env.overrides.copy()
        overrides.update(
            NAME=target_name,
            _RPM_FILENAME=filename,
            VERSION=target_version,
            RELEASE=target_release,
            PKG_FILES=pkg_nodes,  # PKG_FILES just makes it easier to build the spec file
        )
        tmp = spec_in+pkg_nodes
        api.output.verbose_msgf(["rpm-scanner", "scanner"], "Calling RPM Spec generator with: {}",
                                common.DelayVariable(lambda: [e.ID for e in tmp]))

        ################
        # Generate the .spec file name
        if spec_in:
            spec_in = [spec_in[0]]
            spec_file = [env.File('${{BUILD_DIR}}/_rpm/{0}/SPECS/{1}'.format(base_name, spec_in[0].name))]
        else:
            spec_in = []
            spec_file = [env.File('${{BUILD_DIR}}/_rpm/{0}/SPECS/{0}.spec'.format(base_name))]

        if not spec_file[0].isBuilt:
            spec_file = env._rpmspec(
                spec_file,
                tmp,
                **overrides
            )
        api.output.verbose_msgf(["rpm-scanner", "scanner"], "Returned {}",
                                common.DelayVariable(lambda: [e.ID for e in (tar_file + spec_file)]))

        ret = tar_file + spec_file
        g_cache[node.ID] = ret

    return ret


RPMScanner = SCons.Script.Scanner(rpm_scanner, path_function=rpm_group_values, scan_check=rpm_scan_check)


# Mapping for the target architecture with dictionary of known architectures
# depending on the $TARGET_ARCH
# the returned value is what RPM should like

def rpmarch(env, target_arch):
    arch_map_rpm = {}
    arch_map_rpm.update(glb.arch_map)
    arch_mapper = dict(list(env['PKG_ARCH_MAPPER'].items()) + list(env.get('arch_mapper', {}).items()))

    def implicit_rpm_mapping(target_arch):
        rpm_arch = None
        if not arch_mapper:
            rpm_arch = platform.machine()
        arch_map_rpm[target_arch] = rpm_arch
        return rpm_arch

    def explicit_rpm_mapping(target_arch):
        rpm_arch = None
        if target_arch in arch_map_rpm:
            rpm_arch = arch_mapper[target_arch]
            arch_map_rpm[target_arch] = rpm_arch
        return rpm_arch

    try:
        # explicit mapping: when the given architecture maps to arch_map_rpm for the system
        # it uses the corresponding value for target_arch
        # else if the key is not in arch_map_rpm (glb.arch_map), it maps to the new value
        if target_arch == arch_mapper[target_arch]:
            if arch_map_rpm.get(target_arch) == arch_mapper.get(target_arch):
                new_target_arch = target_arch

        elif target_arch in arch_map_rpm:
            if arch_mapper.get(target_arch) is not None:
                arch_map_rpm[target_arch] = explicit_rpm_mapping(target_arch)
                new_target_arch = arch_map_rpm[target_arch]

    except KeyError:
            # implicit mapping: when the given architecture is none,
            # the key maps to the platform system architecture
        arch_map_rpm[target_arch] = implicit_rpm_mapping(target_arch)
        new_target_arch = arch_map_rpm[target_arch]
    return new_target_arch


def rpm_emitter(target, source, env):
    # store stack info to help with error later
    env['_parts_user_stack'] = errors.GetPartStackFrameInfo()

    ####################
    # validate target name
    ####################

    # make sure we have only one target
    if len(target) > 1:
        raise SCons.Errors.UserError('Only one target is allowed.')

    ####################
    # get the dist value
    try:
        dist = subprocess.check_output(["rpm", "--eval", "%{?dist}"]).strip().decode()
    except BaseException:
        api.output.error_msg("rpm tool was not found. Did you install it?")

    # set dist to what is expected
    if ("DIST" in env and env.subst('$DIST') == "%{?dist}") or ("DIST" not in env):
        env["DIST"] = dist

    # map arch to value the RPM will want to use
    if not platform_info.ValidatePlatform(env['TARGET_ARCH']):
        api.output.warning_msgf("{} is not a known defined TARGET_ARCH", env['TARGET_ARCH'])
    env['TARGET_ARCH'] = rpmarch(env, env['TARGET_ARCH'])
    api.output.verbose_msgf(['rpm'], "mapping architecture to rpm value of: {0}", env['TARGET_ARCH'])

    # give us the rpm name without the path on it
    fname = target[0].name

    # making sure we have .rpm on the end of the file name
    # We are also making the correct target path, this allows many different RPM
    # to be correct built without name conflicts
    # the finial value should like $build_dir/_rpm/<rpm_name>/<rpm_name>.rpm
    if str(fname).endswith('.rpm'):
        target = [env.Dir("_rpm/{0}".format(fname[:-4])).File(fname)]
    else:
        target = [env.Dir("_rpm/{0}".format(fname)).File(fname + ".rpm")]

    # validate RPM name
    api.output.verbose_msgf(['rpm'], "validating string value of: {0}", target[0].name)
    grps = re.match(rpm_reg, target[0].name, re.IGNORECASE)
    if grps is None:
        api.output.error_msg(
            "RPM target files must be in format of <name>-<version>-<release>.<arch>.rpm\n current format of value of target file is '{0}'".format(target[0].name))

    ################################
    # export the values
    # to help with more automated depends mapping
    target_name = env.subst(grps.group(1))
    if target_name.endswith(env.subst("${RPM_DEVEL_EXT}")):
        env.ExportItem("PKG_RPM_DEVEL", target_name)
    else:
        env.ExportItem("PKG_RPM", target_name)

    env.ExportItem("RPM_PACKAGE_RUNPATH", env.subst("$PACKAGE_LIB"))

    # set the (override) env _PACKAGE_RUNPATH to use _RPM_RUNPATH
    # by default _PACKAGE_RUNPATH only maps the user values in PACKAGE_RUNPATH
    # we add this value to add the auto gen value given that PACKAGE_AUTO_RUNPATH
    # is True, else the user is setting up everything as they want it
    if env.get("PACKAGE_AUTO_RUNPATH", True):
        env.AppendUnique(_PACKAGE_RUNPATH=['$_RPM_RUNPATH'])

    # add the sources to the group builder
    source = [env.GroupBuilder(src)[0] for src in source]
    return target, source


rpm_action = SCons.Action.Action([
    'mkdir -p ${TARGET.dir}/BUILD',
    ('rpmbuild  --define "_topdir ${TARGET.Dir(\".\").abspath}" '
     '--define "_rpmdir ${TARGET.Dir(\".\").abspath}" '
     '--define "_build_name_fmt %%{Name}-%%{Version}-%%{Release}.%%{Arch}.rpm" -bb '
     '--target=${TARGET_ARCH} ${TARGET.dir}/SPECS/*')])

# internal rpm package builder... meant to be called by RPMPackage function internally
api.register.add_builder('_RPMPackage', SCons.Builder.Builder(
    action=rpm_action,
    source_factory=SCons.Node.Python.Value,
    target_factory=SCons.Node.FS.File,
    target_scanner=RPMScanner,
    emitter=rpm_emitter,
    suffix='.rpm')
)

api.register.add_variable('PKG_ARCH_MAPPER', {}, '')
api.register.add_variable('RPM_DEVEL_EXT', "-devel", "")

# wrapper to help with compatibility


def RpmPackage_wrapper(env, target, source=None, **kw):
    if not source and "sources" in kw:
        source = kw["sources"]
        del kw["sources"]
        api.output.warning_msg("Builders should use 'source' not 'sources'")
    return env._RPMPackage(target, source, **kw)


SConsEnvironment.RPMPackage = RpmPackage_wrapper

api.register.add_variable(
    "_RPM_SELF_ORIGIN_RUNPATH",
    "${GEN_PKG_RUNPATHS('$PACKAGE_LIB',bin_path='$PACKAGE_BIN')}",
    "The relative location for where the package is installed, normally $ORIGIN/../lib",
)
api.register.add_variable(
    "_RPM_DEPENDS_ORIGIN_RUNPATH",
    "${GEN_PKG_RUNPATHS('$RPM_PACKAGE_RUNPATH',bin_path='$PACKAGE_BIN')}",
    "The relative location of dependent packages normally something like '$ORIGIN../../otherpkg/lib' give /opt based installed",
)
api.register.add_variable(
    "_RPM_SELF_ABS_RUNPATH",
    "${GEN_PKG_RUNPATHS('$PACKAGE_LIB',bin_path='$PACKAGE_BIN',use_origin=False)}",
    "The absolute path to the default package install location"
)
api.register.add_variable(
    "_RPM_DEPENDS_ABS_RUNPATH",
    "${GEN_PKG_RUNPATHS('$RPM_PACKAGE_RUNPATH',bin_path='$PACKAGE_BIN', use_origin=False)}",
    "The absolute path dependent default package install locations"
)
api.register.add_variable(
    "RPM_RUNPATH",
    ["$_RPM_SELF_ORIGIN_RUNPATH", "$_RPM_DEPENDS_ORIGIN_RUNPATH", "$_RPM_SELF_ABS_RUNPATH", "$_RPM_DEPENDS_ABS_RUNPATH"],
    "The set of path to use for the packages RUNPATH. Can be changed to control what is used and order"
)
api.register.add_variable(
    "_RPM_RUNPATH",
    "${JOIN('$RPM_RUNPATH',':')}",
    "The final path value as a string"
)

api.register.add_variable(
    'RPM_PACKAGE_RUNPATH', [],
    'The runpath values of dependent packages that we need to add to the runpath added by the user')
