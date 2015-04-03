import glb
import common
import core.util as util
import api.output
import settings

import policy

import SCons.Script


g_package_groups = {}

_packaging_groups = dict(), dict()

def PackageGroups():
    return g_package_groups.keys()

def PackageGroup(name,parts=None):
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
                api.output.verbose_msg('packaging','Adding to PackageGroup :"{0}" Part: "{1}"'.format(name,p))
            else:
                raise RuntimeError("%s does not refer to a defined Part" % (p))

        #cache is out of date..  zap it to force rebuild
        if name in _packaging_groups[0]:
            map(dict.clear, _packaging_groups)

    return tuple(x for x in result)

# global form
def ReplacePackageGroupCriteria(name,func):
    name = SCons.Script.DefaultEnvironment().subst(name)
    settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name] = common.make_list(func)
    return PackageGroup(name)

def AppendPackageGroupCriteria(name,func):
    name = SCons.Script.DefaultEnvironment().subst(name)
    try:
        settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name].extend(common.make_list(func))
    except:
        settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name] = common.make_list(func)
    return PackageGroup(name)

def PrependPackageGroupCriteria(name,func):
    name = SCons.Script.DefaultEnvironment().subst(name)
    try:
        settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name] = common.make_list(func) + settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name]
    except:
        settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name] = common.make_list(func)
    return PackageGroup(name)



# env form
def ReplacePackageGroupCriteriaEnv(env,name,func):
    name = env.subst(name)
    env['PACKAGE_GROUP_FILTER'][name] = common.make_list(func)
    return PackageGroup(name)

def AppendPackageGroupCriteriaEnv(env,name,func):
    name = env.subst(name)
    try:
        env['PACKAGE_GROUP_FILTER'][name].extend(common.make_list(func))
    except:
        env['PACKAGE_GROUP_FILTER'][name] = common.make_list(func)
    return PackageGroup(name)

def PrependPackageGroupCriteriaEnv(env,name,func):
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
                    'While forming "{0}" package found files included by multiple groups: \n{1}'.format(target, '\n'.join('\t{0} is included by groups: {1}'.format(file, ', '.join(sorted(groups))) for (file, groups) in sorted(duplicates.iteritems()))),
                    stackframe = stackframe)
        return sorted(visited.iterkeys()), sorted(duplicates.iteritems())
    klass.GetFilesFromPackageGroups = GetFilesFromPackageGroups
    return klass

def GetPackageGroupFiles(name,no_pkg=False):
    '''
    Get all the file that are installed that are define as part of a group.
    This function will try to cache known result to improve speed.
    '''
    # get Cache value
    groups = _packaging_groups[int(bool(no_pkg))]
    try:
        return list(groups[name])
    except KeyError:
        # no cache value..  re build list
        api.output.verbose_msg('packaging','Sorting PackageGroup Parts into nodes')
        SortPackageGroups()


    # return what we got, if not in rebuilt list return empty list
    return list(groups.get(name, set()))

def get_group_set(name, no_pkg):
    group = _packaging_groups[bool(no_pkg)]
    try:
        return group[name]
    except KeyError:
        group[name] = result = set()
        _packaging_groups[bool(not no_pkg)][name] = set()
        return result

def SortPackageGroups():
    grps = PackageGroups() # get the groups

    # reset the cache
    for group in _packaging_groups:
        group.clear()

    for name in grps:
        #get the component that are part of the group
        obj_lst = PackageGroup(name)
        api.output.verbose_msg('packaging','Sorting Group:',name)

        for obj in obj_lst:
            if isinstance(obj,SCons.Node.FS.File):
                files = [obj]
                map_objs = glb.engine.def_env.get('PACKAGE_GROUP_FILTER',[])
            else: # assume this is a part
                pobj = glb.engine._part_manager._from_alias(obj)
                map_objs = pobj.Env.get('PACKAGE_GROUP_FILTER',[])
                # this needs to be updated with we add teh new format ( and
                # lots of different section types)
                files = pobj.Section('build').InstalledFiles
            
            for f in files:
                # ATTENTION: for performance reasons we inline
                # metatag.MetaTag() function in this code.
                try:
                    package = f.attributes.package
                except AttributeError:
                    _no_pkg, group_val = False, set()
                    f.attributes.package = package = common.namespace(no_package=_no_pkg, group=group_val)
                else:
                    _no_pkg, group_val = package.get('no_package', False), package.get('group', set())

                # Add file to group
                if util.isString(group_val): # Check most common case first
                    get_group_set(group_val, _no_pkg).add(f)
                elif not group_val:

                    # Set default meta-tag value
                    package.update(group=name)

                    for group, tests in map_objs.iteritems():
                        for test in tests:
                            if test(f):
                                group_val.add(group)
                                get_group_set(group, _no_pkg).add(f)
                                break
                    if not group_val:
                        group_val = set([name])
                        get_group_set(name, _no_pkg).add(f)
                    #apply meta tag to file
                    package.update(group=list(group_val))
                else:
                    # group_val is asserted to be a list or a set
                    for group in group_val:
                        get_group_set(group, _no_pkg).add(f)
                api.output.verbose_msgf(["packaging-mapping"],"{0} add to group(s)={1}, no_pkg={2}",f.ID,group_val,_no_pkg)

def GetPackageGroupFiles_env(env,name,no_pkg=False):
    return GetPackageGroupFiles(name,no_pkg)

# compatible for mistakes
def ReplacePackageGroupCritera(name,func):
    api.output.warning_msg('ReplacePackageGroupCritera is deprecated, use ReplacePackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return ReplacePackageGroupCriteria(name,func)

def AppendPackageGroupCritera(name,func):
    api.output.warning_msg('AppendPackageGroupCritera is deprecated, use AppendPackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return AppendPackageGroupCriteria(name,func)

def PrependPackageGroupCritera(name,func):
    api.output.warning_msg('PrependPackageGroupCritera is deprecated, use PrependPackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return PrependPackageGroupCriteria(name,func)


def ReplacePackageGroupCriteriaEnv_old(env,name,func):
    api.output.warning_msg('ReplacePackageGroupCritera is deprecated, use ReplacePackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return env.ReplacePackageGroupCriteria(name,func)
def AppendPackageGroupCriteriaEnv_old(env,name,func):
    api.output.warning_msg('AppendPackageGroupCritera is deprecated, use AppendPackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return env.AppendPackageGroupCriteria(name,func)
def PrependPackageGroupCriteriaEnv_old(env,name,func):
    api.output.warning_msg('PrependPackageGroupCritera is deprecated, use PrependPackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return env.PrependPackageGroupCriteria(name,func)


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
api.register.add_variable('PACKAGE_ROOT',"/", "")

api.register.add_variable('PACKAGE_LIB', '${PACKAGE_ROOT}/lib', '')
api.register.add_variable('PACKAGE_BIN', '${PACKAGE_ROOT}/bin', '')

api.register.add_variable('PACKAGE_TOOLS','${PACKAGE_ROOT}/tools','')
api.register.add_variable('PACKAGE_API','${PACKAGE_ROOT}/API','')
api.register.add_variable('PACKAGE_INCLUDE','${PACKAGE_ROOT}/include','')
api.register.add_variable('PACKAGE_CONFIG','${PACKAGE_ROOT}/config','')
api.register.add_variable('PACKAGE_DOC','${PACKAGE_ROOT}/doc','')
api.register.add_variable('PACKAGE_HELP','${PACKAGE_ROOT}/help','')
api.register.add_variable('PACKAGE_MANPAGE','${PACKAGE_ROOT}/man','')
api.register.add_variable('PACKAGE_MESSAGE','${PACKAGE_ROOT}/message','')
api.register.add_variable('PACKAGE_RESOURCE','${PACKAGE_ROOT}/resource','')
api.register.add_variable('PACKAGE_SAMPLE','${PACKAGE_ROOT}/samples','')
api.register.add_variable('PACKAGE_DATA','${PACKAGE_ROOT}/data','')
api.register.add_variable('PACKAGE_TOP_LEVEL','${PACKAGE_ROOT}/','')
api.register.add_variable('PACKAGE_PYTHON','${PACKAGE_ROOT}/python','')
api.register.add_variable('PACKAGE_SCRIPT','${PACKAGE_ROOT}/scripts','')

api.register.add_variable('PACKAGE_NAME','unknown','')
api.register.add_variable('PACKAGE_VERSION','0.0.0','')

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

