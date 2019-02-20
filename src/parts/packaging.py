from __future__ import absolute_import, division, print_function

import parts.api as api
import parts.common as common
import parts.core.util as util
import parts.glb as glb
import parts.policy as policy
import parts.settings as settings
import SCons.Script
from SCons.Environment import SubstitutionEnvironment as SubstEnv
from SCons.Script.SConscript import SConsEnvironment

# this is the group to part mapping
# ie this is the unsorted data
g_package_groups = {}

# this is a tuple of no_pkg,pkg dict of {groupName:Node.File}
_sorted_groups = dict(), dict()


def PackageGroups():
    return list(g_package_groups.keys())


def PackageGroup(name, parts=None):
    '''
    Currently is bound to only handling Parts or Componnet objects ( as these
    allow to refer to a certain Part) The idea of allowing the addition of Files
    or Dir ( and like items) are not being handled at this time as we really
    don't know where we want to put the files in the package.
    '''

    name = SCons.Script.DefaultEnvironment().subst(name)
    if not name:
        return []

    try:
        result = g_package_groups[name]
    except KeyError:
        g_package_groups[name] = result = set()

    if parts:
        parts = common.make_list(parts)
        for p in parts:
            if util.isString(p):
                result.add(p)
                api.output.verbose_msg('packaging', 'Adding to PackageGroup :"{0}" Part: "{1}"'.format(name, p))
            else:
                raise RuntimeError("%s does not refer to a defined Part" % (p))

        # cache is out of date..  zap it to force rebuild
        if name in _sorted_groups[0]:
            _clear_sorted_group()

    return tuple(x for x in result)

# global form


def AddPackageNodeFilter(callbacks):
    try:
        settings.DefaultSettings().vars['PACKAGE_NODE_FILTER'].Default.extend(common.make_list(callbacks))
    except BaseException:
        settings.DefaultSettings().vars['PACKAGE_NODE_FILTER'] = common.make_list(callbacks)


def ReplacePackageGroupCriteria(name, func):
    name = SCons.Script.DefaultEnvironment().subst(name)
    settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name] = common.make_list(func)
    return PackageGroup(name)


def AppendPackageGroupCriteria(name, func):
    name = SCons.Script.DefaultEnvironment().subst(name)
    try:
        settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name].extend(common.make_list(func))
    except BaseException:
        settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name] = common.make_list(func)
    return PackageGroup(name)


def PrependPackageGroupCriteria(name, func):
    name = SCons.Script.DefaultEnvironment().subst(name)
    try:
        settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name] = common.make_list(
            func) + settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name]
    except BaseException:
        settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name] = common.make_list(func)
    return PackageGroup(name)


# env form
def ReplacePackageGroupCriteriaEnv(env, name, func):
    name = env.subst(name)
    env['PACKAGE_GROUP_FILTER'][name] = common.make_list(func)
    return PackageGroup(name)


def AppendPackageGroupCriteriaEnv(env, name, func):
    name = env.subst(name)
    try:
        env['PACKAGE_GROUP_FILTER'][name].extend(common.make_list(func))
    except BaseException:
        env['PACKAGE_GROUP_FILTER'][name] = common.make_list(func)
    return PackageGroup(name)


def PrependPackageGroupCriteriaEnv(env, name, func):
    name = env.subst(name)
    try:
        env['PACKAGE_GROUP_FILTER'][name] = common.make_list(func) + env['PACKAGE_GROUP_FILTER'][name]
    except BaseException:
        env['PACKAGE_GROUP_FILTER'][name] = common.make_list(func)
    return PackageGroup(name)


def GetFilesFromPackageGroups(target, groups, no_pkg=False, stackframe=None):
    return SCons.Script.DefaultEnvironment().GetFilesFromPackageGroups(target, groups, no_pkg, stackframe)


def def_GetFilesFromPackageGroups(klass):
    def GetFilesFromPackageGroups(env, target, groups, no_pkg=False, stackframe=None):
        '''
        Returns tuple: (files, duplicates). files is list of Node objects
        specified in the groups. duplicates is a list each item of which is
        a tuple of duplicated Node object and list of groups where the Node object
        is referenced.

        If env's subst variable PACKAGE_DUPLICATE_FILES_HANDLING is set to "error"
        the function will through SCons.Errors.UserError exception.
        If the variable is set to "warning" the function will only output a message
        to stderr and log file.
        '''
        visited = dict()
        duplicates = dict()
        for group in groups:
            files = GetPackageGroupFiles(group)
            intersection = set(visited.keys()) & set(files)
            for file in intersection:
                duplicates[file] = (duplicates.get(file) or (visited[file],)) + (group,)
            visited.update((file, group) for file in files)
        if duplicates:
            try:
                multigroup_policy = getattr(policy.ReportingPolicy,
                                            env.get('PACKAGE_DUPLICATE_FILES_HANDLING'))
            except (TypeError, AttributeError):
                multigroup_policy = policy.ReportingPolicy.ignore
            api.output.policy_msg(
                multigroup_policy,
                'packaging',
                'While forming "{0}" package found files included by multiple groups: \n{1}'.format(
                    target,
                    '\n'.join(
                        '\t{0} is included by groups: {1}'.format(
                            file,
                            ', '.join(
                                sorted(groups))) for (
                            file,
                            groups) in sorted(
                            duplicates.items()))),
                stackframe=stackframe)
        return sorted(visited.keys()), sorted(duplicates.items())
    klass.GetFilesFromPackageGroups = GetFilesFromPackageGroups
    return klass


def GetPackageGroupFiles(name, no_pkg=False):
    '''
    Get all the file that are installed that are define as part of a group.
    This function will try to cache known result to improve speed.
    '''
    # get Cache value
    groups = _sorted_groups[int(bool(no_pkg))]
    try:
        return list(groups[name])
    except KeyError:
        # no cache value..  re build list
        api.output.verbose_msg('packaging', 'Sorting PackageGroup Parts into nodes')
        SortPackageGroups()

    # return what we got, if not in rebuilt list return empty list
    return list(groups.get(name, set()))

# this get the set of files for a given group


def get_group_set(name, no_pkg):
    group = _sorted_groups[bool(no_pkg)]
    try:
        return group[name]
    except KeyError:
        # don't have the group
        # set both no_pkg and pkg cases
        group[name] = result = set()
        _sorted_groups[bool(not no_pkg)][name] = set()
        return result


def _clear_sorted_group():
    _sorted_groups[0].clear()
    _sorted_groups[1].clear()


def _filter_by_criteria(node, filters, metainfo):
    api.output.verbose_msgf(["packaging"], "Filtering node via Group {0}", node.ID)
    no_pkg = metainfo.get('no_package', False)
    for group, tests in filters.items():
        # test if there is a filter to move this to a different group
        for test in tests:
            if test(node):
                api.output.verbose_msgf(["packaging-filter"],
                                        "Criteria filter mapped {0} add to group={1}, no_pkg={2}", node.ID, group, no_pkg)
                get_group_set(group, no_pkg).add(node)
                # update node meta info with package info
                # based on criteria filter replacing everything
                metainfo.update(groups=(group,))
                return True
    return False


def _filter_node(node, filters, metainfo):
    '''
    call each filter on the node
    the returned value from the filter may be a string or (string,Boolean)
    in which the boolean is if the node should be 'no_pkg'ed for the group
    '''

    api.output.verbose_msgf(["packaging"], "Filtering node {0}", node.ID)
    new_groups = set(metainfo.get('groups', set()))
    default_no_pkg = metainfo.get('no_package', False)
    for _filter in filters:
        grps = _filter(node)
        if grps:
            for group_info in grps:
                try:
                    group, no_pkg = group_info
                except ValueError:
                    group, no_pkg = group_info, default_no_pkg
                api.output.verbose_msgf(["packaging-filter"],
                                        "Node filter mapped {0} to group={1}, no_pkg={2}", node.ID, group, no_pkg)
                get_group_set(group, no_pkg).add(node)
                new_groups.add(group)
    metainfo.update(groups=tuple(new_groups))


def _get_file_entries(node):
    # walk the Dir node to see what nodes it contains
    # return a flat list of file node
    ret = []
    for k, v in node.entries.items():
        if isinstance(v, SCons.Node.FS.Dir) and k != ".." and k != ".":
            ret.extend(_get_file_entries(v))
        else:  # this is a File node
            ret.append(v)
    return ret


def SortPackageGroups():
    # get the set of groups currently defined
    grps = PackageGroups()

    # reset the cache
    _clear_sorted_group()

    group_filters = glb.engine.def_env.get('PACKAGE_GROUP_FILTER', {})
    node_filters = glb.engine.def_env.get('PACKAGE_NODE_FILTER', [])

    # for each node that is "installed"
    for node in SCons.Tool.install._INSTALLED_FILES:
        api.output.verbose_msgf(["packaging"], "Mapping node {0}", node.ID)
        try:
            # get the package object
            metainfo = node.attributes.package
        except AttributeError:
            # if it does not exist set the value for group and no_pkg default values
            # we should see this case... but to be safe
            node.attributes.package = metainfo = common.namespace()

        part_alias = metainfo.part_alias
        no_pkg = metainfo.get('no_package', False)
        pobj = glb.engine._part_manager._from_alias(part_alias)
        # the default group to map this to
        part_grp = pobj.PackageGroup

        # does it have a Metatag value forcing it to a group(s)?
        # if so we use this and we don't do a criteria filter
        if "groups" in metainfo:
            for group in metainfo.groups:
                get_group_set(group, no_pkg).add(node)
        elif "group" in metainfo:
            get_group_set(metainfo.group, no_pkg).add(node)
        elif not _filter_by_criteria(node, group_filters, metainfo):
            get_group_set(part_grp, no_pkg).add(node)
            metainfo.update(groups=(part_grp,))
            api.output.verbose_msgf(["packaging-mapping"], "{0} add to group(s)={1}, no_pkg={2}", node.ID, part_grp, no_pkg)
        # run the node filter on the node to add it to any extra groups
        _filter_node(node, node_filters, metainfo)

    return


def GetPackageGroupFiles_env(env, name, no_pkg=False):
    return GetPackageGroupFiles(name, no_pkg)

# compatible for mistakes


def ReplacePackageGroupCritera(name, func):
    api.output.warning_msg('ReplacePackageGroupCritera is deprecated, use ReplacePackageGroupCriteria',
                           "(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return ReplacePackageGroupCriteria(name, func)


def AppendPackageGroupCritera(name, func):
    api.output.warning_msg('AppendPackageGroupCritera is deprecated, use AppendPackageGroupCriteria',
                           "(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return AppendPackageGroupCriteria(name, func)


def PrependPackageGroupCritera(name, func):
    api.output.warning_msg('PrependPackageGroupCritera is deprecated, use PrependPackageGroupCriteria',
                           "(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return PrependPackageGroupCriteria(name, func)


def ReplacePackageGroupCriteriaEnv_old(env, name, func):
    api.output.warning_msg('ReplacePackageGroupCritera is deprecated, use ReplacePackageGroupCriteria',
                           "(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return env.ReplacePackageGroupCriteria(name, func)


def AppendPackageGroupCriteriaEnv_old(env, name, func):
    api.output.warning_msg('AppendPackageGroupCritera is deprecated, use AppendPackageGroupCriteria',
                           "(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return env.AppendPackageGroupCriteria(name, func)


def PrependPackageGroupCriteriaEnv_old(env, name, func):
    api.output.warning_msg('PrependPackageGroupCritera is deprecated, use PrependPackageGroupCriteria',
                           "(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return env.PrependPackageGroupCriteria(name, func)


SConsEnvironment.GetPackageGroupFiles = GetPackageGroupFiles_env

def_GetFilesFromPackageGroups(SubstEnv)

SConsEnvironment.ReplacePackageGroupCritera = ReplacePackageGroupCriteriaEnv_old
SConsEnvironment.AppendPackageGroupCritera = AppendPackageGroupCriteriaEnv_old
SConsEnvironment.PrependPackageGroupCritera = PrependPackageGroupCriteriaEnv_old

SConsEnvironment.ReplacePackageGroupCriteria = ReplacePackageGroupCriteriaEnv
SConsEnvironment.AppendPackageGroupCriteria = AppendPackageGroupCriteriaEnv
SConsEnvironment.PrependPackageGroupCriteria = PrependPackageGroupCriteriaEnv


# these tell the packging system locations to use on the user to map install location for a real install on that system
# basically it maps the INSTALL_ROOT to the current "real system" location to use in the packaging code
# TODO ... update the Var to map based on target platform
api.register.add_variable('PACKAGE_ROOT', "/", "")

api.register.add_variable('PACKAGE_LIB', '${PACKAGE_ROOT}/$INSTALL_LIB_SUBDIR', '')
api.register.add_variable('PACKAGE_BIN', '${PACKAGE_ROOT}/$INSTALL_BIN_SUBDIR', '')
api.register.add_variable('PACKAGE_PRIVATE_BIN', '${PACKAGE_ROOT}/$INSTALL_PRIVATE_BIN_SUBDIR', '')

api.register.add_variable('PACKAGE_TOOLS', '${PACKAGE_ROOT}/$INSTALL_TOOLS_SUBDIR', '')
api.register.add_variable('PACKAGE_API', '${PACKAGE_ROOT}/$INSTALL_API_SUBDIR', '')
api.register.add_variable('PACKAGE_INCLUDE', '${PACKAGE_ROOT}/$INSTALL_INCLUDE_SUBDIR', '')
api.register.add_variable('PACKAGE_CONFIG', '${PACKAGE_ROOT}/$INSTALL_CONFIG_SUBDIR', '')
api.register.add_variable('PACKAGE_DOC', '${PACKAGE_ROOT}/$INSTALL_DOC_SUBDIR', '')
api.register.add_variable('PACKAGE_HELP', '${PACKAGE_ROOT}/$INSTALL_HELP_SUBDIR', '')
api.register.add_variable('PACKAGE_MANPAGE', '${PACKAGE_ROOT}/$INSTALL_MANPAGE_SUBDIR', '')
api.register.add_variable('PACKAGE_MESSAGE', '${PACKAGE_ROOT}/$INSTALL_MESSAGE_SUBDIR', '')
api.register.add_variable('PACKAGE_RESOURCE', '${PACKAGE_ROOT}/$INSTALL_RESOURCE_SUBDIR', '')
api.register.add_variable('PACKAGE_SAMPLE', '${PACKAGE_ROOT}/$INSTALL_SAMPLE_SUBDIR', '')
api.register.add_variable('PACKAGE_DATA', '${PACKAGE_ROOT}/$INSTALL_DATA_SUBDIR', '')
api.register.add_variable('PACKAGE_TOP_LEVEL', '${PACKAGE_ROOT}/', '')
api.register.add_variable('PACKAGE_PYTHON', '${PACKAGE_ROOT}/$INSTALL_PYTHON_SUBDIR', '')
api.register.add_variable('PACKAGE_SCRIPT', '${PACKAGE_ROOT}/$INSTALL_SCRIPT_SUBDIR', '')

api.register.add_variable('PACKAGE_NAME', 'unknown', '')
api.register.add_variable('PACKAGE_VERSION', '0.0.0', '')

api.register.add_variable('PACKAGE_GROUP_FILTER', {}, "")
api.register.add_variable('PACKAGE_NODE_FILTER', [], "")


api.register.add_global_object('PackageGroups', PackageGroups)
api.register.add_global_object('PackageGroup', PackageGroup)
api.register.add_global_object('GetPackageGroupFiles', GetPackageGroupFiles)
api.register.add_global_object('GetFilesFromPackageGroups', GetFilesFromPackageGroups)

api.register.add_global_object('AddPackageNodeFilter', AddPackageNodeFilter)

api.register.add_global_object('ReplacePackageGroupCritera', ReplacePackageGroupCritera)
api.register.add_global_object('AppendPackageGroupCritera', AppendPackageGroupCritera)
api.register.add_global_object('PrependPackageGroupCritera', PrependPackageGroupCritera)

api.register.add_global_object('ReplacePackageGroupCriteria', ReplacePackageGroupCriteria)
api.register.add_global_object('AppendPackageGroupCriteria', AppendPackageGroupCriteria)
api.register.add_global_object('PrependPackageGroupCriteria', PrependPackageGroupCriteria)
