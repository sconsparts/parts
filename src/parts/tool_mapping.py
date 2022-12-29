

import os

import parts.api as api
import parts.common as common
import parts.core.util as util
import parts.load_module as load_module
import SCons.Tool
from SCons.Errors import UserError
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment


def get_tlset_module(tlchain, version):
    # first try to load exact match.. then general match
    if version:
        name_list = [tlchain + "_" + version, tlchain]
    else:
        name_list = [tlchain]

    # The list of tool-chain site directories will not change during
    # this session. Cache it.
    global __toolchain_dirs
    try:
        __toolchain_dirs
    except NameError:
        __toolchain_dirs = load_module.get_site_directories('toolchain')

    for name in name_list:
        try:
            return load_module.load_module(__toolchain_dirs, name, 'toolchain')
        except (ImportError, UserError):
            pass

    return None


def get_tools(env, tlset):

    # for each tool see if the value is a tool, or abstaction
    # this is done via testing is a tool exist with that name
    # this is to prevent loops like cl->msvc->cl->msvc etc...
    # ("name",None) -> tool chain
    # ("name","val") -> tool chain
    # ("name",{}) ->tool
    # ("name",functor) ->tool

    # The list of tools site directories will not change during
    # this session. Cache it.
    global __tools_dirs
    try:
        __tools_dirs
    except NameError:
        __tools_dirs = load_module.get_site_directories('tools')
    new_list = []
    repeat = False
    for tool in tlset:
        try:
            tool, configuration = tool
        except ValueError:
            assert len(tool) == 3
            new_list.append(tool)
            continue
        else:
            configured = True
        if configuration is None or util.isString(configuration):
            # get the list subst for the value
            repeat = True
            mod = get_tlset_module(tool, configuration)
            # check to see if loaded a chain mapping
            if mod:
                new_list.extend(mod.resolve(env, configuration))
            else:
                # see if this is a tool that is loadable
                try:
                    SCons.Tool.Tool(tool, toolpath=__tools_dirs)
                except Exception:
                    api.output.error_msg("Failed to load Unknown ToolChain or Tool:", tool, show_stack=False)
                else:
                    new_list.extend([(tool, {}, configured)])
        else:
            # This has been handled
            new_list.append((tool, configuration, configured))

    if repeat:
        return get_tools(env, new_list)
    # returns in the end [(tool_str,{of what to apply first} or functor(env)),...]
    return new_list


def _ToolChain(env, chainlist):
    # resolve tool chain into the list of tools to setup
    # normalize for of all tools requested
    tlset = common.process_tool_arg(chainlist)
    # get the list
    tool_list = get_tools(env, tlset)

    try:
        configured_tools = env['CONFIGURED_TOOLS']
    except KeyError:
        # env object does not have setdefault method
        env['CONFIGURED_TOOLS'] = configured_tools = list()

    # add tools to the environment
    for tool_name, configuration, configured in tool_list:
        # apply pre tool configurtation part so the tool will setup correctly
        if configuration is None:
            pass
        elif util.isDictionary(configuration):
            env.Replace(**configuration)
        else:
            configuration(env)
        # this is a small hack that allow items like mstool to
        # not have the MS compiler add its value to the environment
        # when the Configuration() call happens
        if configured:
            # apply the tool to the Environment
            configured_tools.append(tool_name)
        tool = SCons.Tool.Tool(tool_name, toolpath=env['toolpath'])
        env['_BUILD_CONTEXT_FILES'].add(tool.generate.__code__.co_filename)
        tool(env)


def tool_converter(str_val, raw_val):
    if util.isString(raw_val):
        tmp = raw_val.split(',')
        lst = []
        for i in tmp:
            lst.append(i.split('_'))
        return lst
    if util.isList(raw_val):
        return raw_val
    raise "Invalid tool value '%s'" % raw_val


# adding logic to Scons Environment object
api.register.add_method(_ToolChain,'ToolChain')


api.register.add_variable('toolchain', ['default'], 'The tool chain to use by default', converter=tool_converter)
