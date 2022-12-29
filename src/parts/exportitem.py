

import re

import parts.api as api
import parts.common as common
import parts.core.util as util
import parts.errors as errors
import parts.glb as glb
import SCons.Script
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment


class EXPORT_TYPES:
    FILE = 1
    PATH = 2
    PATH_FILE = 3


def export_path(env, target_dirs, source_dirs, sobj, prop, use_src=False, create_sdk=True):

    # We have three case basically of type of paths we pass
    # 1) is the SDK/final path for the file
    # 2) is the build path for the file
    # 3) is the source path of the file
    ret = []

    # we assume that this is only used in cases of list
    export_table = sobj.Exports.setdefault(prop,[[]])[0]
    if use_src:  # ie use Raw Source Directories
        for s in source_dirs:
            # setting up the libpaths
            # print s,env.Dir(s).abspath
            if s not in export_table:
                target_dir = env.Dir(s).srcnode().abspath
                export_table.append(target_dir)
                api.output.verbose_msg(['export.path','export'], f"Exporting path from {sobj.ID}:\n {prop} = {target_dir}")
            # we want to return the SDK directories
            # when we need to create an SDK.
            if create_sdk == True:
                for t in target_dirs:
                    # make this a node
                    if util.isString(t):
                        t = env.Dir(t)
                    final_path = t.srcnode()
                    if final_path not in export_table:
                        target_dir = final_path
                        ret.append(target_dir)
    else:
        for t in target_dirs:
            # make this a node
            if util.isString(t):
                t = env.Dir(t)

            build_path = t
            final_path = t.srcnode()

            if create_sdk == False:
                # use build directory
                if build_path not in export_table:
                    target_dir = build_path
                    export_table.append(target_dir)
                    api.output.verbose_msg(['export.path','export'], f"Exporting path from {sobj.ID}:\n {prop} = {target_dir}")

            elif final_path not in export_table:
                target_dir = final_path
                export_table.append(target_dir)
                api.output.verbose_msg(['export.path','export'], f"Exporting path from {sobj.ID}:\n {prop} = {target_dir}")
                ret.append(target_dir)

    return ret


_reg = re.compile(r'[\w\-\+\.]*.so.([0-9]+\.[0-9]+\.[0-9]*|[0-9]+\.[0-9]+|[0-9]+)', re.I)


def export_file(env, targets, sobj, prop):
    ret = []
    for target in targets:
        if util.isString(target):
            target = env.File(target)
        file = target.name
        ret.append(file)

        if file.endswith('.so') or file.endswith('.sl'):
            file = file[:-3]
        elif _reg.match(file):
            # if this matches we want to not add this file
            # as doing this would upset the linker
            continue
        elif getattr(target.attributes, 'FilterAs', None):
            continue
        try:
            sobj.Exports[prop][0] += [file]
        except KeyError:
            sobj.Exports[prop] = [[file]]
        api.output.verbose_msg(['export.file','export'], f"Exporting file from {sobj.ID}:\n {prop} = {file}")
    return ret


def export_file_path(env, targets, sobj, prop, use_src):
    ret = []
    prop_val = []
    for t in targets:
        if util.isString(t):
            t = env.File(t)
        build_path = t
        final_path = t.srcnode()
        ret.append(final_path)
        if use_src == False:
            # use build directory
            if build_path not in sobj.Exports[prop]:
                prop_val.append(build_path)
        elif final_path not in sobj.Exports[prop]:
            prop_val.append(final_path)
    env.ExportItem(prop, prop_val, create_sdk=False, map_as_dependance=True)
    return ret


def ExportCPPPATH(env, values, create_sdk=True):
    values = env.arg2nodes(values, env.fs.Dir)
    return ExportItem(env, 'CPPPATH', values, create_sdk)


def ExportLIBPATH(env, values, create_sdk=True):
    values = env.arg2nodes(values, env.fs.Dir)
    return ExportItem(env, 'LIBPATH', values, create_sdk)


def ExportCPPDEFINES(env, values, create_sdk=True):
    return ExportItem(env, 'CPPDEFINES', values, create_sdk)


def ExportCFLAGS(env, values, create_sdk=True):
    return ExportItem(env, 'CFLAGS', values, create_sdk)


def ExportCCFLAGS(env, values, create_sdk=True):
    return ExportItem(env, 'CCFLAGS', values, create_sdk)


def ExportCXXFLAGS(env, values, create_sdk=True):
    return ExportItem(env, 'CXXFLAGS', values, create_sdk)


def ExportLINKFLAGS(env, values, create_sdk=True):
    return ExportItem(env, 'LINKFLAGS', values, create_sdk)


def ExportLIBS(env, values, create_sdk=True):
    return ExportItem(env, 'LIBS', values, create_sdk)


def ExportItem(env, variable, values, create_sdk=True, map_as_dependance=False):  # , public=False):
    '''

    @param env The current environment
    @param variable The variable name we want to export
    @param values The values to map to the variable. Can be an picklable item, including self contained functions, and SCons node objects
    @param create_sdk map this information in to the auto generated SDK parts file


    This function adds to the export table of a given part the variable and it values. If the variable exists in the environment already and is a list or is the values is
    a list type then the values will be made into a list, flatten and appended all unique items to the list. Otherwise the data will replace any existing data. If data does
    exist, there will be a verbose message that can be printed out.
    '''

    errors.SetPartStackFrameInfo(True)
    sobj = glb.engine._part_manager.section_from_env(env)

    # test to see if the variable or value should be a list.
    # ie if the variable is a list in the Environment, we want this to be a list here
    if util.isList(values) or util.isList(env.get(variable)):

        values = common.make_list(values)
        if variable in ('CPPPATH', 'LIBPATH'):
            values = env.arg2nodes(values, env.fs.Dir)
        #map(lambda x:  _map_group(x,variable),values)
        if (variable in sobj.Exports) == False:
            sobj.Exports[variable] = [[]]
        # this is not a list already.. make it one
        if util.isList(sobj.Exports[variable]) == False:
            tmp = [common.make_list(sobj.Exports[variable])]
            sobj.Exports[variable] = tmp
            api.output.verbose_msg(['export'], f"Exporting from {sobj.ID}:\n {variable} = {[str(v) for v in tmp]}")

        # add our values
        # common.extend_unique(sobj.Exports[variable],values)
        sobj.Exports[variable][0] += values
        api.output.verbose_msg(['export'], f"Exporting from {sobj.ID}:\n {variable} = {[str(v) for v in values]}")

    else:
        if variable in sobj.Exports:
            api.output.verbose_msg(
                ['export'],
                f'"{sobj.ID}" already has variable "{variable}" in export table, overriding with new value')
        sobj.Exports[variable] = values
        api.output.verbose_msg(['export'], f"Exporting from {sobj.ID}:\n {variable} = {values}")

    if map_as_dependance:
        common.append_unique(sobj.ExportAsDepends, variable)
        # remove this as this does not work with "dynamic" builders and requires a post_install_queue
        # which we want to kill/obsolete
        # if values:
        #print("{0}::alias::{1}::{2}".format(env['PART_SECTION'], env['ALIAS'], variable), values)
        #env.Alias("{0}::alias::{1}::{2}".format(env['PART_SECTION'], env['ALIAS'], variable), values)

    # set the create SDK value
    if env['CREATE_SDK'] == False and create_sdk == True:
        create_sdk = False

    errors.ResetPartStackFrameInfo()


# adding logic to Scons Environment object
api.register.add_method(ExportCPPPATH)
api.register.add_method(ExportLIBPATH)
api.register.add_method(ExportCPPDEFINES)
api.register.add_method(ExportCFLAGS)
api.register.add_method(ExportCCFLAGS)
api.register.add_method(ExportCXXFLAGS)
api.register.add_method(ExportLINKFLAGS)
api.register.add_method(ExportLIBS)
api.register.add_method(ExportItem)
