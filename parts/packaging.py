import glb
import common
import core.util as util
import api.output
import settings

import policy

import SCons.Script

# this is the group to part mapping
# ie this is the unsorted data
g_package_groups = {}

# this is a tuple of no_pkg,pkg dict of {groupName:Node.File}
_sorted_groups = dict(), dict()


def PackageGroups():
    return g_package_groups.keys()


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


def ReplacePackageGroupCriteria(name, func):
    name = SCons.Script.DefaultEnvironment().subst(name)
    settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name] = common.make_list(func)
    return PackageGroup(name)


def AppendPackageGroupCriteria(name, func):
    name = SCons.Script.DefaultEnvironment().subst(name)
    try:
        settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name].extend(common.make_list(func))
    except:
        settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name] = common.make_list(func)
    return PackageGroup(name)


def PrependPackageGroupCriteria(name, func):
    name = SCons.Script.DefaultEnvironment().subst(name)
    try:
        settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name] = common.make_list(
            func) + settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name]
    except:
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
    except:
        env['PACKAGE_GROUP_FILTER'][name] = common.make_list(func)
    return PackageGroup(name)


def PrependPackageGroupCriteriaEnv(env, name, func):
    name = env.subst(name)
    try:
        env['PACKAGE_GROUP_FILTER'][name] = common.make_list(func) + env['PACKAGE_GROUP_FILTER'][name]
    except:
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
            intersection = set(visited.iterkeys()) & set(files)
            for file in intersection:
                duplicates[file] = (duplicates.get(file) or (visited[file],)) + (group,)
            visited.update((file, group) for file in files)
        if duplicates:
            try:
                multigroup_policy = getattr(policy.ReportingPolicy,
                                            env.get('PACKAGE_DUPLICATE_FILES_HANDLING'))
            except (TypeError, AttributeError):
                multigroup_policy = policy.ReportingPolicy.ignore
            api.output.policy_msg(multigroup_policy, 'packaging',
                                  'While forming "{0}" package found files included by multiple groups: \n{1}'.format(target, '\n'.join(
                                      '\t{0} is included by groups: {1}'.format(file, ', '.join(sorted(groups))) for (file, groups) in sorted(duplicates.iteritems()))),
                                  stackframe=stackframe)
        return sorted(visited.iterkeys()), sorted(duplicates.iteritems())
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


def _set_file_info(curr_group, f, map_objs):
    # ATTENTION: for performance reasons we inline
    # metatag.MetaTag() function in this code.
    try:
        # get the package object
        package = f.attributes.package
    except AttributeError:
        # if it does not exist set the value for group and no_pkg default values
        _no_pkg, group_val = False, set()
        f.attributes.package = package = common.namespace(no_package=_no_pkg, group=group_val)
    else:
        # we have it.. get values that are set
        _no_pkg, group_val = package.get('no_package', False), package.get('group', set())

    # Add file to group

    # the file has a string tag saying what group it should be in
    # this has to be set manually with a metatag call forcing it
    # to a given group, cannot be filter after this
    if util.isString(group_val):
        get_group_set(group_val, _no_pkg).add(f)
    # group value is not set yet
    # so we will add the current group to it
    elif not group_val:
        # Set default meta-tag value
        # package.update(group=name)

        for group, tests in map_objs.viewitems():
            # test if there is a filter to move this to a different group
            for test in tests:
                if test(f):
                    group_val.add(group)
                    get_group_set(group, _no_pkg).add(f)
                    break
        # if the filter did not set this to a new value
        # set this to a default value of the current group
        if not group_val:
            group_val = set([curr_group])
            get_group_set(curr_group, _no_pkg).add(f)
        # apply meta tag to file
        # we make it a tuple to save space as this will not change during this run
        package.update(group=tuple(group_val))
    else:
        # group_val is asserted to be a tuple or a set
        # Map the value in to the different groups it has been mapped to
        for group in group_val:
            get_group_set(group, _no_pkg).add(f)
    api.output.verbose_msgf(["packaging-mapping"], "{0} add to group(s)={1}, no_pkg={2}", f.ID, group_val, _no_pkg)

# make this a util function ( been copied and pasted around a little)


def _get_file_entries(node):
    # walk the Dir node to see what nodes it contains
    # return a flat list of file node
    ret = []
    for k, v in node.entries.viewitems():
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

    for name, obj_lst in g_package_groups.viewitems():
        # get the Part Objects
        api.output.verbose_msg('packaging', 'Sorting Group:', name)
        for obj in obj_lst:
            if util.isFile(obj):
                files = [obj]
                map_objs = glb.engine.def_env.get('PACKAGE_GROUP_FILTER', [])
            # elif util.isDir(obj): fill in when we can
            #    files = [obj]
            #    map_objs = glb.engine.def_env.get('PACKAGE_GROUP_FILTER',[])
            else:
                # else we assume this is a string for a part alias/ID
                pobj = glb.engine._part_manager._from_alias(obj)
                map_objs = pobj.Env.get('PACKAGE_GROUP_FILTER', [])
                # this needs to be updated with we add the new format
                # as we will have different section other than build
                # at moment we assume utest sectiond don't package
                # this will be come a look to go over all defined sections
                files = pobj.Section('build').InstalledFiles

            for f in files:
                _set_file_info(name, f, map_objs)
                # this needs to be called in a scanner for this to work
                # if util.isFile(obj):
                #    _set_file_info(name,f,map_objs)
                # elif util.isDir(obj):
                #    # get all items in the directory and apply
                #    for i in _get_file_entries(f):
                #        _set_file_info(name,i,map_objs)


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


from SCons.Script.SConscript import SConsEnvironment


SConsEnvironment.GetPackageGroupFiles = GetPackageGroupFiles_env

from SCons.Environment import SubstitutionEnvironment as SubstEnv
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

api.register.add_global_object('PackageGroups', PackageGroups)
api.register.add_global_object('PackageGroup', PackageGroup)
api.register.add_global_object('GetPackageGroupFiles', GetPackageGroupFiles)
api.register.add_global_object('GetFilesFromPackageGroups', GetFilesFromPackageGroups)

api.register.add_global_object('ReplacePackageGroupCritera', ReplacePackageGroupCritera)
api.register.add_global_object('AppendPackageGroupCritera', AppendPackageGroupCritera)
api.register.add_global_object('PrependPackageGroupCritera', PrependPackageGroupCritera)

api.register.add_global_object('ReplacePackageGroupCriteria', ReplacePackageGroupCriteria)
api.register.add_global_object('AppendPackageGroupCriteria', AppendPackageGroupCriteria)
api.register.add_global_object('PrependPackageGroupCriteria', PrependPackageGroupCriteria)
