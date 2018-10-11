'''
This contain the base code for all configurations we define in parts, and
some helpfunction to help dump data, or get the correct configuration data
'''

import common
import core.util
import version
import configurations
import api.output
import load_module

import SCons.Script

import os
import traceback
import StringIO
import pprint
import copy

from SCons.Debug import logInstanceCreation

from platform_info import SystemPlatform


def null_ver_mapper(env):
    return '0.0.0'


# this is an internal trick to make the configuration object look like a function
# but to have it instead store it self in a global map
g_configuration = {}


def ConfigValues(**kw):
    return kw


class configuration(object):

    def __init__(self, default_ver_func, post_process_func=None):
        if __debug__:
            logInstanceCreation(self)
        self.default_ver_func = default_ver_func
        self.post_process_func = post_process_func
        self.ver_rng = {}

    def map_none_version(self, env):
        return self.default_ver_func(env)

    def VersionRange(self, ver_rng, replace={}, filter={}, append={}, prepend={},
                     prepend_env={}, append_env={}, post_process_func=None):
        self.ver_rng[version.version_range(ver_rng)] = {
            'append': append,
            'prepend': prepend,
            'replace': replace,
            'filter': filter,
            'append_env': append_env,
            'prepend_env': prepend_env,
            'post_process_func': post_process_func
        }

    def merge(self, ver, cfg):
        '''
        Merge setting values with given base values passed in via the
        cfg variable
        '''

        # need range for store key later
        ver_rng = version.version_range()
        for v_range, val in self.ver_rng.iteritems():
            if ver in v_range:
                mysetting = val
                ver_rng = v_range
                break
        else:
            return cfg, version.version_range()

        settings = cfg[0]
        settings_ex = cfg[1]

        # setup settings_ex
        tmp = mysetting['post_process_func']
        if ('post_process_func' in settings_ex) == False:
            settings_ex['post_process_func'] = []
        if tmp is not None:
            settings_ex['post_process_func'].append(tmp)
        if self.post_process_func is not None:
            settings_ex['post_process_func'].append(self.post_process_func)

        settings_ex['default_ver_func'] = []
        if self.default_ver_func is not None:  # should not be None.. clean up latter
            settings_ex['default_ver_func'].append(self.default_ver_func)

        tmp = mysetting['prepend_env']
        settings_ex['prepend_env'] = []
        if tmp is not None:
            settings_ex['prepend_env'].append(tmp)

        tmp = mysetting['append_env']
        settings_ex['append_env'] = []
        if tmp is not None:
            settings_ex['append_env'].append(tmp)

        # process normal flags settings
        # we process this in a for of:
        # {flag:{replace:val or [],append:[],prepend:[]}
        tmp = mysetting['replace']
        if tmp != {}:
            for k, v in tmp.iteritems():
                settings[k] = {'replace': v, 'append': [], 'prepend': []}

        tmp = mysetting['filter']
        if tmp != {}:
            for k, v in tmp.iteritems():
                data = settings.get(k, {})
                for i in v:
                    for dk, dv in data.iteritems():
                        if i in dv:
                            dv.remove(i)

        tmp = mysetting['append']
        if tmp != {}:
            for k, v in tmp.iteritems():
                if (k in settings) == False:
                    settings[k] = {'append': [], 'prepend': []}
                settings[k]['append'].extend(v)

        tmp = mysetting['prepend']
        if tmp != {}:
            for k, v in tmp.iteritems():
                if (k in settings) == False:
                    settings[k] = {'append': [], 'prepend': []}
                v.extend(settings[k]['prepend'])
                settings[k]['prepend'] = v

        return (settings, settings_ex), ver_rng


class _ConfigurationSet(object):

    def __init__(self, name, dependsOn):
        if __debug__:
            logInstanceCreation(self)
        self.name = name
        # add note if depends on is a list.. only support single base
        self.depends = dependsOn
        self.map = {}
        self.defining_file = None

    def has_tool(self, tool):
        # if the key exists it has been loaded.. however the tool
        # may have a value of None
        return tool in self.map

    def has_tool_cfg(self, tool, host, target, ver=None):

        # first see if we have matching tool
        tool_config = self.map.get(tool, None)
        if tool_config is None:
            # no tool defined.. return None so master logic can fallback
            return False

        # next find the host
        host_config = tool_config.get(host, None)
        if host_config is None:
            # Don't have anything for this tool to configure
            return False

        # next we find the target
        target_config = host_config.get(target, None)
        if target_config is None:
            # Don't have anything for this tool to configure
            return False

        if ver is not None:
            # check to see if there is a version match
            v_rng = target_config['versions']
            for vr in v_rng:
                if ver in vr:
                    return True
            else:
                return False

        return True

    def Dependent(self):
        return self.depends

    def Name(self):
        return self.name

    def DefiningFile(self):
        return self.defining_file

    def add_config_setting(self, tool, ver_rng, host, target, settings, ver_mapper, files):
        if tool in self.map:
            if host in self.map[tool]:
                if target in self.map[tool][host]:
                    if 'versions' in self.map[tool][host][target]:
                        if ver_rng in self.map[tool][host][target]['versions']:
                            self.map[tool][host][target]['versions'][ver_rng].update(settings)
                            self.map[tool][host][target]['default_ver_func'] = ver_mapping
                            self.map[tool][host][target]['defining_files'] = files
                        else:
                            self.map[tool][host][target]['versions'][ver_rng] = settings
                            self.map[tool][host][target]['default_ver_func'] = ver_mapper
                            self.map[tool][host][target]['defining_files'] = files
                    else:
                        self.map[tool][host][target].update({
                            "default_ver_func": ver_mapper,
                            "versions": {ver_rng: settings},
                            'defining_files': files

                        })
                else:
                    self.map[tool][host].update({target: {
                        "default_ver_func": ver_mapper,
                        "versions": {ver_rng: settings},
                        'defining_files': files
                    }})
            else:
                self.map[tool].update({host: {target: {
                    "default_ver_func": ver_mapper,
                    "versions": {ver_rng: settings},
                    'defining_files': files
                }}})
        else:
            self.map[tool] = {host:
                              {
                                  target:
                                  {
                                      "default_ver_func": ver_mapper,
                                      "versions": {ver_rng: settings},
                                      'defining_files': files
                                  }
                              }
                              }

    def get_config_setting(self, env, tool, ver, host, target):

        # first see if we have matching tool
        tool_config = self.map.get(tool, None)
        if tool_config is None:
            # no tool defined.. return None so master logic can fallback
            return None

        # next find the host
        host_config = tool_config.get(host, None)
        if host_config is None:
            # Don't have anything for this tool to configure
            return None

        # next we find the target
        target_config = host_config.get(target, None)
        if target_config is None:
            # Don't have anything for this tool to configure
            return None

        # next we get the version range list
        versions = target_config.get('versions', None)
        if versions is None:
            return None

        # map version if set to None to best value based on mapping function
        if ver is None:
            ver = target_config['default_ver_func'](env)
        # see if we have a match with the version.
        ver_config = None
        for v_range in versions.keys():
            if ver in v_range:
                ver_config = versions[v_range]
                break
        else:
            return None

        return copy.deepcopy(ver_config)

    def resolve_version(self, tool, host, target, env):
        # this should be called because we check that such as config existed first
        # tool_config=self.map.get(tool,None)
        return self.map[tool][host][target]['default_ver_func'](env)

    def defining_files(self, tool, host, target):
        '''
        this is called to get the files that define this configuration
        We want this to help with quick configuration up-to-date checks latter
        '''
        # tool_config=self.map.get(tool,None)
        return self.map[tool][host][target]['defining_files']


def DefineConfiguration(name, dependsOn='default'):
    # add configuration
    if name in g_configuration:
        print "ConfigurationSet", name, " already exists"
        # warning is it exists?
    # add dependance
    g_configuration[name] = _ConfigurationSet(name, dependsOn)


def load_cfg(name):
    '''
    This function loads the information from the DefineConfiguration()
    to get the relationships of the defined configruation. This tells
    us what base configurations we need to load first and merge setting
    with.
    '''
    # stop any loop/crashes that might happen if loading a None cfg
    if name is None:
        return
    # load the configuration meta information
    api.output.verbose_msg('configuration', "Loading configuration definition for <%s>" % name)
    configurations.configuration(name)
    # make sure any dependent config is loaded as well
    dep = g_configuration[name].Dependent()

    if (dep in g_configuration) == False and dep is not None:
        load_cfg(dep)


def make_name_list(tool, host, target):
    # TODO: make this generate
    host, target = [SystemPlatform(str(x)) for x in (host, target)]
    nl = [
        tool + "_" + host.OS + "-" + host.ARCH + "_" + target.OS + "-" + target.ARCH,
        tool + "_" + host.OS + "-" + host.ARCH + "_" + target.OS + "-" + 'any',
        tool + "_" + host.OS + "-" + 'any' + "_" + target.OS + "-" + target.ARCH,
        tool + "_" + host.OS + "-" + 'any' + "_" + target.OS + "-" + 'any',

        tool + "_" + host.OS + "-" + host.ARCH + "_" + 'any' + "-" + target.ARCH,
        tool + "_" + host.OS + "-" + host.ARCH + "_" + 'any' + "-" + 'any',
        tool + "_" + host.OS + "-" + host.ARCH + "_" + 'any',
        tool + "_" + host.OS + "-" + host.ARCH,
        tool + "_" + host.OS + "-" + 'any' + "_" + 'any' + "-" + target.ARCH,
        tool + "_" + host.OS + "-" + 'any' + "_" + 'any' + "-" + 'any',
        tool + "_" + host.OS + "-" + 'any' + "_" + 'any',
        tool + "_" + host.OS + "-" + 'any',

        tool + "_" + 'any' + "-" + host.ARCH + "_" + target.OS + "-" + target.ARCH,
        tool + "_" + 'any' + "-" + host.ARCH + "_" + target.OS + "-" + 'any',
        tool + "_" + 'any' + "-" + 'any' + "_" + target.OS + "-" + target.ARCH,
        tool + "_" + 'any' + "_" + target.OS + "-" + target.ARCH,
        tool + "_" + 'any' + "-" + 'any' + "_" + target.OS + "-" + 'any',
        tool + "_" + 'any' + "_" + target.OS + "-" + 'any',

        tool + "_" + 'any' + "-" + host.ARCH + '_' + 'any' + "-" + target.ARCH,
        tool + "_" + 'any' + "-" + host.ARCH + '_' + 'any' + "-" + 'any',
        tool + "_" + 'any' + "-" + host.ARCH + '_' + 'any',
        tool + "_" + 'any' + "-" + host.ARCH,
        tool + "_" + 'any' + "-" + 'any' + '_' + 'any' + "-" + target.ARCH,
        tool + "_" + 'any' + '_' + 'any' + "-" + target.ARCH,
        tool + "_" + 'any' + "-" + 'any' + '_' + 'any' + "-" + 'any',
        tool + '_any_any',
        tool + '_any',
        tool
    ]
    return nl


def make_name_dict(tool, host, target):
    nl = {
        tool + "_" + host.OS + "-" + host.ARCH + "_" + target.OS + "-" + target.ARCH:
        (tool, host.OS, host.ARCH, target.OS, target.ARCH),
        tool + "_" + host.OS + "-" + host.ARCH + "_" + target.OS + "-" + 'any':
        (tool, host.OS, host.ARCH, target.OS, None),
        tool + "_" + host.OS + "-" + 'any' + "_" + target.OS + "-" + target.ARCH:
        (tool, host.OS, None, target.OS, target.ARCH),
        tool + "_" + host.OS + "-" + 'any' + "_" + target.OS + "-" + 'any':
        (tool, host.OS, None, target.OS, None),

        tool + "_" + host.OS + "-" + host.ARCH + "_" + 'any' + "-" + target.ARCH:
        (tool, host.OS, host.ARCH, None, target.ARCH),
        tool + "_" + host.OS + "-" + host.ARCH + "_" + 'any' + "-" + 'any':
        (tool, host.OS, host.ARCH, None, None),
        tool + "_" + host.OS + "-" + host.ARCH + "_" + 'any':
        (tool, host.OS, host.ARCH, None, None),
        tool + "_" + host.OS + "-" + host.ARCH:
        (tool, host.OS, host.ARCH, None, None),
        tool + "_" + host.OS + "-" + 'any' + "_" + 'any' + "-" + target.ARCH:
        (tool, host.OS, None, None, target.ARCH),
        tool + "_" + host.OS + "-" + 'any' + "_" + 'any' + "-" + 'any':
        (tool, host.OS, None, None, None),
        tool + "_" + host.OS + "-" + 'any' + "_" + 'any':
        (tool, host.OS, None, None, None),
        tool + "_" + host.OS + "-" + 'any':
        (tool, host.OS, None, None, None),

        tool + "_" + 'any' + "-" + host.ARCH + "_" + target.OS + "-" + target.ARCH:
        (tool, None, host.ARCH, target.OS, target.ARCH),
        tool + "_" + 'any' + "-" + host.ARCH + "_" + target.OS + "-" + 'any':
        (tool, None, host.ARCH, target.OS, None),
        tool + "_" + 'any' + "-" + 'any' + "_" + target.OS + "-" + target.ARCH:
        (tool, None, None, target.OS, target.ARCH),
        tool + "_" + 'any' + "_" + target.OS + "-" + target.ARCH:
        (tool, None, None, target.OS, target.ARCH),
        tool + "_" + 'any' + "-" + 'any' + "_" + target.OS + "-" + 'any':
        (tool, None, None, target.OS, None),
        tool + "_" + 'any' + "_" + target.OS + "-" + 'any':
        (tool, None, None, target.OS, None),

        tool + "_" + 'any' + "-" + host.ARCH + '_' + 'any' + "-" + target.ARCH:
        (tool, None, host.ARCH, None, target.ARCH),
        tool + "_" + 'any' + "-" + host.ARCH + '_' + 'any' + "-" + 'any':
        (tool, None, host.ARCH, None, None),
        tool + "_" + 'any' + "-" + host.ARCH + '_' + 'any':
        (tool, None, host.ARCH, None, None),
        tool + "_" + 'any' + "-" + host.ARCH:
        (tool, None, host.ARCH, None, None),
        tool + "_" + 'any' + "-" + 'any' + '_' + 'any' + "-" + target.ARCH:
        (tool, None, None, None, target.ARCH),
        tool + "_" + 'any' + '_' + 'any' + "-" + target.ARCH:
        (tool, None, None, None, target.ARCH),
        tool + "_" + 'any' + "-" + 'any' + '_' + 'any' + "-" + 'any':
        (tool, None, None, None, None),
        tool + '_any_any':
        (tool, None, None, None, None),
        tool + '_any':
        (tool, None, None, None, None),
        tool:
        (tool, None, None, None, None)
    }
    return nl


def found_config_files(name, tool, host, target):
    '''
    Just see if we can find the file that would be loaded, if any.
    This is more for build context testing. To see if something changed
    '''
    ret = set()
    dep = g_configuration[name].Dependent()
    if dep is not None:
        ret = found_config_files(dep, tool, host, target)
    name_list = make_name_list(tool, host, target)
    pathList = load_module.get_site_directories(os.path.join('configurations', name))
    typeName = 'config%s'.format(name)

    for path in pathList:
         # for each path we need to see if the module we might care about exists here
        loc_modules = load_module.get_possible_modules([path])
        for configName in name_list:
            if configName in loc_modules:
                try:
                    api.output.verbose_msg('configuration', "trying to load file <%s.py>" % configName)
                    mod = load_module.load_module(pathList, configName, typeName)
                    if mod.__file__.endswith('.py'):
                        ret.add(os.path.abspath(mod.__file__))
                    else:
                        ret.add(os.path.abspath(mod.__file__)[:-1])
                    break
                except ImportError:
                    pass
                except:
                    api.output.verbose_msg("configuration", "Unexpected failure:\n",
                                           traceback.format_exc())

    return ret


def load_tool_config(env, name, tool, host, target):
    '''
    Load all infomation about a given tool in to a memory cache.
    Will load all information in file about different version.
    A note on speed up for later tweaks is that we probally want to
    store the merged data in a datacache, and load from there as needed
    to help save memory and processing time.
    '''
    ################################################
    # First we need to start by loading base config

    # get dependent config, None is there is no dependent
    dep = g_configuration[name].Dependent()
    base_settings = ({}, {})
    base_ver_mapper = null_ver_mapper
    if dep is not None:  # we have a dependent
        # Did we load the dependent information already?
        if not g_configuration[dep].has_tool_cfg(tool, host, target):
            # if not, we need to load it
            load_tool_config(env, dep, tool, host, target)

    ################################################
    # Now the base config (if any) is loaded; we need to load the current confirguation

    api.output.verbose_msgf('configuration',
                            "Loading configuration <{0}> for tool <{1}>", name, tool)

    # get list of possible file name forms to try load
    name_list = make_name_list(tool, host, target)
    found = False
    ver = None
    mod = None
    pathList = load_module.get_site_directories(os.path.join('configurations', name))
    typeName = 'config{0}'.format(name)

    # for each path we want to see if on of the set of files we want exists
    # if not we load the next path
    for path in pathList:
        api.output.verbose_msgf('configuration', "Looking in path {0}", path)
        # for each path we need to see if the module we might care about exists here
        loc_modules = load_module.get_possible_modules([path])
        for configName in name_list:
            if configName in loc_modules:
                # we have a possible hit.. try to load it
                try:
                    api.output.verbose_msgf('configuration', "trying to load file <{0}.py>", configName)
                    mod = load_module.load_module(pathList, configName, typeName)
                    api.output.verbose_msgf('configuration',
                                            'Configuration <{0}> loaded! File <{1}>', name, mod.__file__)
                # clean up exceptions...
                except ImportError:
                    continue
                except SyntaxError:
                    raise
                except:
                    api.output.verbose_msg("configuration", "Unexpected failure:\n",
                                           traceback.format_exc())
                    continue

                # Load our config data, and map the version value
                # g_config_context[tool]=mod.__file__
                if mod.__file__.endswith('.py'):
                    files = set([mod.__file__])
                else:
                    files = set([mod.__file__[:-1]])
                # get version based on value in environment
                ver = mod.config.map_none_version(env)
                found = True
                break
            else:
                # we don't have any configruation files.
                # we make note of this as we will store empty setting for this case later
                # or setting based on dependent values
                files = set()
                # reports that for this configruation there was not special data defined
                # api.output.verbose_msg('configuration',
                # 'Configuration <%s> found no configuration for tool <%s>' % (name, configName))
                found = False  # nothing found
        if found:
            break

    #############################################################
    # At this point we want to get all information for the different versions
    # and store this information.

    if dep is not None:
        # Get base settings
        api.output.verbose_msg(['configuration_setup'],
                               'Getting dependent configuration settings', dep)
        base_settings = g_configuration[dep].get_config_setting(env, tool, ver, host, target)
        api.output.verbose_msg('configuration_setup', 'Got Settings of:', base_settings)
        files.update(g_configuration[dep].defining_files(tool, host, target))

    if found:
        # merge setting
        api.output.verbose_msg('configuration_setup', "Merging configurtation settings")
        settings, ver_rng = mod.config.merge(ver, base_settings)
        api.output.verbose_msg(['configuration_setup'], 'Got Settings of:', settings)
        api.output.verbose_msg('configuration_setup', "Storing settings")
        g_configuration[name].add_config_setting(tool, ver_rng, host, target, settings,
                                                 mod.config.default_ver_func, files)
    else:
        api.output.verbose_msg('configuration_setup', "Storing settings")
        g_configuration[name].add_config_setting(tool, version.version_range(), host, target,
                                                 base_settings, base_ver_mapper, files)


def get_config(env, name, tool, host, target):
    ver = None
    # is "meta" config loaded. ie the data about the configuration relationships
    # and other properties
    if (name in g_configuration) == False:
        # if not load it this information
        load_cfg(name)
    # Get the information we now have stored
    config = g_configuration[name]

    # dif we load information about the tool for a given host-target combination?
    if config.has_tool_cfg(tool, host, target) == False:
        # if not load all information about this tool
        ver = load_tool_config(env, name, tool, host, target)
    # if version is None get a real version
    if ver is None:
        api.output.trace_msgf('configuration', "No version defined for tool {0}", tool)
        ver = config.resolve_version(tool, host, target, env)
        api.output.trace_msgf('configuration', "Resolved version for tool {0} to {1}", tool, ver)
        if config.has_tool_cfg(tool, host, target, ver) == False:
            # if not load all information about this tool
            ver = load_tool_config(env, name, tool, host, target)
    files = config.defining_files(tool, host, target)

    # get settings
    settings = config.get_config_setting(env, tool, ver, host, target)
    if settings is None:
        return ({}, {}), files
    return settings, files


def get_defining_config_files(name, tool, host, target):
    '''
    This function just gets the file defining a configuration
    Which is needed for testing purposes configuratition context.
    '''
    # is "meta" config loaded
    if (name in g_configuration) == False:
        # if not load it
        load_cfg(name)
    # is tool loaded?
    return found_config_files(name, tool, host, target)

# compatibility object


class config_type_wrapper(str, common.bindable):

    def __eq__(self, rhs):
        api.output.warning_msg(
            "Please use isConfigBasedOn() to test if configuration is based on debug or release, next drop will match exact configuration for == test", env=self.env)
        return self.env.isConfigBasedOn(rhs)

    def __ne__(self, rhs):
        api.output.warning_msg(
            "Please use isConfigBasedOn() to test if configuration is based on debug or release, next drop will match exact configuration for != test", env=self.env)
        return self.env.isConfigBasedOn(rhs) == False

    def _rebind(self, env, key):
        '''
        Rebind the environment to a new one.
        There does not seem a way to have this happen in a clone
        as from what i can see semi_deep_copy does not pass a new env
        However I can do this in cases when i do a copy, which is not as
        bad as not doing it at all
        '''
        import copy
        tmp = config_type_wrapper(copy.copy(self))
        tmp._bind(env, key)
        return tmp

    def _bind(self, env, key):
        self.__dict__['env'] = env


def apply_config(env, name=None):
    global g_config_context
    g_config_context = {}
    # get tools set to configure
    tools = env['CONFIGURED_TOOLS']
    # print "Configured Tool to get configuration from",tools
    host = env['HOST_PLATFORM']
    target = env['TARGET_PLATFORM']

    if name is None:
        env['CONFIG'] = env.subst('${CONFIG}')
        name = env['CONFIG']
    else:
        env['CONFIG'] = name

    env['CONFIG'] = config_type_wrapper(name)
    env['CONFIG']._bind(env, 'CONFIG')

    api.output.verbose_msg('configuration', "Applying configuration <%s>" % name)
    # print "tools that have been configured",tools
    for t in tools:
        tmp, files = get_config(env, name, t, host, target)
        settings, setting_extra = tmp
        # print t,settings,setting_extra
        try:
            env['_CONFIG_CONTEXT'][t] = files
        except KeyError:
            env['_CONFIG_CONTEXT'] = {}
            env['_CONFIG_CONTEXT'][t] = files

        for flag, items in settings.iteritems():
            # replace values
            if 'replace' in items:
                env.Replace(**{flag: items['replace']})
            if 'append' in items:
                env.AppendUnique(**{flag: items['append']})
            # prepend values in env
            if 'prepend' in items:
                env.PrependUnique(**{flag: items['prepend']})

        tmp = setting_extra.get('prepend_env', {})
        for i in tmp:
            for k, v in i.iteritems():
                env.PrependENVPath(k, v, delete_existing=True)

        tmp = setting_extra.get('append_env', {})
        for i in tmp:
            for k, v in i.iteritems():
                env.AppendENVPath(k, v, delete_existing=True)

        tmp = setting_extra.get('post_process_func', [])
        for f in tmp:
            f(env)


def _isconfigbasedon(env, name, config):
    try:
        tmp = g_configuration[config]
    except KeyError:
        load_cfg(name)
        tmp = g_configuration[config]
    if tmp.Name() == name:
        return True
    if tmp.Dependent() is not None:
        return _isconfigbasedon(env, name, tmp.Dependent())
    else:
        return False


def isConfigBasedOn(env, name):
    return _isconfigbasedon(env, name, env.subst('$CONFIG'))


# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.isConfigBasedOn = isConfigBasedOn
SConsEnvironment.Configuration = apply_config

api.register.add_variable(['CONFIG', 'config'], '${default_config}', 'The configuration to use')
api.register.add_variable('default_config', 'debug', 'The configuration to use by default')

api.register.add_global_parts_object('ConfigValues', ConfigValues)
api.register.add_global_object('ConfigValues', ConfigValues)
