
# this implements My first attempt at the IAPAT object
# i caling it Settings as this in the end is what this does
# it deal with the logic of different ways to setup/configure/defines
# a set of setting used to define a Environment contect to build within

import glb
import api
import Variables
import common
import core.util as util
import load_module
#import platform_info

from SCons.Debug import logInstanceCreation

import SCons.Script

import copy
import os
import sys


def normalize_map(m):
    ''' doesn't do anything but look for certain key that might be in different
    forms and translate them to a common one'''
    key = 'mode'
    value = m.get(key, None)
    if util.isString(value) and not util.isList(value):
        m[key] = value.split(',')

    key = 'toolchain'
    value = m.get(key, None)
    if util.isString(value) and not util.isList(value):
        tmp = common.process_tool_arg(value.split(','))
        tmp.reverse()
        m[key] = tmp

    return m


# primary config stuff

# class to handle old stuff that needs to change.. move to better location later
class deprecated(object):

    def __init__(self, key, new_key, value):
        if __debug__:
            logInstanceCreation(self)
        self.key = key
        self.new_key = new_key
        self._value = value

    def __str__(self):
        # errors.SetPartStackFrameInfo()
        api.output.warning_msg("[", self.key, "] is deprecated please use [", self.new_key, "]")
        # errors.ResetPartStackFrameInfo()
        return self._value

    def __eq__(self, rhs):
        api.output.warning_msg("[", self.key, "] is deprecated please use [", self.new_key, "]")
        return self._value == rhs

    def __ne__(self, rhs):
        api.output.warning_msg("[", self.key, "] is deprecated please use [", self.new_key, "]")
        return self._value != rhs

    def __hash__(self):
        api.output.warning_msg("[", self.key, "] is deprecated please use [", self.new_key, "]")
        return hash(str(self._value))

    def __len__(self):
        api.output.warning_msg("[", self.key, "] is deprecated please use [", self.new_key, "]")
        return len(str(self._value))

    def __getitem__(self, key):
        api.output.warning_msg("[", self.key, "] is deprecated please use [", self.new_key, "]")
        return self._value[key]

    def __add__(self, other):
        api.output.warning_msg("[", self.key, "] is deprecated please use [", self.new_key, "]")
        return self._value + other

    def __radd__(self, other):
        api.output.warning_msg("[", self.key, "] is deprecated please use [", self.new_key, "]")
        return other + self._value

    def __contains__(self, item):
        api.output.warning_msg("[", self.key, "] is deprecated please use [", self.new_key, "]")
        return item in self._value


class string_tester(object):

    def __init__(self, value):
        if __debug__:
            logInstanceCreation(self)
        self.value = value

    def __eq__(self, rhs):
        import fnmatch
        return fnmatch.fnmatchcase(rhs, self.value)


def get_cache_values(*lst):
    cache_values = [
        string_tester('*'),
        string_tester('TARGET_*'),
        string_tester('*_VERSION'),
        string_tester('*_SCRIPT'),
        string_tester('*_INSTALL_ROOT'),
        'use_env',
        'config',
        'CONFIG',
        'toolchain',
        'tools',  # to be removed
        'ARCHITECTURE',  # to be removed
        'PLATFORM'  # for safety in SCons
    ]
    ret = ''
    for l in lst:
        for i in l:
            if i in cache_values:
                ret += "%s=%s" % (i, l[i])

    return ret


class ToolChain():

    def __init__(self):
        if __debug__:
            logInstanceCreation(self)

    def Exists(name, **kw):
        pass


class All:

    def __init__(self, *lst):
        if __debug__:
            logInstanceCreation(self)
        self.lst = lst

    def Valid(self, tester):
        for i in self.lst:
            if tester(i) == False:
                return False
        return True

    def GetValues(self):
        return self.lst


class OneOf:

    def __init__(self, *lst):
        if __debug__:
            logInstanceCreation(self)
        self.lst = lst

    def Valid(self, tester):
        for i in self.lst:
            if tester(i) == True:
                return True
        return False

    def GetValues(self, tester):
        for i in self.lst:
            if tester(i) == True:
                return [i]
        return []


class AnyOf:

    def __init__(self, *lst):
        if __debug__:
            logInstanceCreation(self)
        self.lst = lst

    def Valid(self, tester):
        for i in self.lst:
            if tester(i) == True:
                return True
        return False

    def GetValues(self, tester):
        ret = []
        for i in self.lst:
            if tester(i) == True:
                ret.append(i)
        return ret


# move to a new file to remove core.py

class parts_dict(dict):

    def __init__(self, *args, **kw):
        if __debug__:
            logInstanceCreation(self)
        dict.__init__(self, *args, **kw)

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        if is_dictionary(value):
            self[name] = parts_dict(value)
        else:
            self[name] = value

    def __delattr__(self, name):
        del self[name]

opt_true_values = set(['y', 'yes', 'true', 't', '1', 'on', 'all'])
opt_false_values = set(['n', 'no', 'false', 'f', '0', 'off', 'none'])


class Settings(object):

    __env_chache = {}

    def __init__(self):
        if __debug__:
            logInstanceCreation(self)
        # dict.__init__(self,kw)

        # cfg_files=[SCons.Script.GetOption('cfg_file')]
        # vars=Variables.Variables(cfg_files,args=overrides,user_defaults=glb.defaultoverides)

        self.vars = Variables.Variables()
        self.vars._on_change.Connect(self._handle_var_change)
        self.options = SCons.Script.Main.OptionsParser.values
        self.__addshellpath = True
        self.__env_cache = {}

    # stuff for self.value logic
# def __getattr__(self,name):
# return self[name]
# def __setattr__(self,name,value):
# self[name]=value
# def __delattr__(self,name):
##        del self[name]

    def SetOptionDefault(self,):
        pass

    @property
    def AddShellPath(self):
        '''
        Tell us if we are going to add the Shell when we create the Environment
        '''
        return self.__addshellpath

    @AddShellPath.setter
    def AddShellPath(self, val):
        '''
        Sets if we are going to add the Shell when we create the Environment
        '''
        self.__addshellpath = val

    # option get --<name>
    def AddOption(self, *lst, **kw):
        return SCons.Script.AddOption(*lst, **kw)

    def BoolOption(self, name, default=None, explict=False, dest=None, help=''):
        '''Constructs a --<option> argument that expects some bool value
        @param option Name of the option
        @param default The default value of this option
        @param explict The user has to say --key=true, --key will not work
        @param dest The name of the value we use to get this value
        @param help The help text for this option

        '''

        def opt_bool(option, opt, value, parser, var):

            TrueValue = True
            if value is None:
                parser.values.__dict__[var] = TrueValue
                return
            tmp = value.lower()
            if tmp in opt_true_values:
                parser.values.__dict__[var] = TrueValue
            elif tmp in opt_false_values:
                parser.values.__dict__[var] = not TrueValue
            else:
                raise OptionValueError('Invalid value for boolean option "%s" value "%s"\n Valid options are %s' %
                                       (var.replace('-', '_'), value, opt_true_values | opt_false_values))

        return SCons.Script.AddOption(name,
                                      dest=dest,
                                      nargs=explict and 1 or '?',
                                      callback=lambda option, opt, value, parser: opt_bool(option, opt, value, parser, dest),
                                      type='string',
                                      action='callback',
                                      help=help)

    def FeatureOption(self, name, default=True, explict=False, dest=None, help=''):

        if default != True and default != False:
            print "Error Default value for Feature has to be a True or False value"

        a = SCons.Script.AddOption("--enable-{0}".format(name),
                                   dest=dest,
                                   default=default,
                                   action="store_true",
                                   help='Enable Parts data to be used cache')

        b = SCons.Script.AddOption("--disable-{0}".format(name),
                                   dest=dest,
                                   default=default,
                                   action="store_false",
                                   help='Disable Parts data cache from being used')

        return [a, b]

    def EnumOption(self, name, choices, default, dest, help):
        return SCons.Script.AddOption(name,
                                      dest=dest,
                                      default=default,
                                      nargs=1,
                                      type='choice',
                                      choices=choices,
                                      action='store',
                                      help=help)

    def ListOption(self, name, default=[], dest=None, help=None):

        def opt_list(option, opt, value, parser, var):
            parser.values.__dict__[var] = value.split(',')

        SCons.Script.AddOption(name,
                               dest=dest,
                               default=default,
                               callback=lambda option, opt, value, parser: opt_list(option, opt, value, parser, 'verbose'),
                               nargs=1,
                               type='string',
                               action='callback',
                               help=help)

    def IntOption(self, name, default=0, dest=None, help=None):

        SCons.Script.AddOption(name,
                               dest=dest,
                               default=default,
                               nargs=1,
                               type='int',
                               action='store',
                               help=help)

    def PathOption(self, *lst, **kw):
        pass

    def GetOption(self, name):
        SCons.Script.GetOption(name)

    # Variables are <name>=Value
    def AddVariable(self, name, help=None, default=None, validator=None, converter=None, value=None, help_group=None):
        self.vars.Add(Variables.Variable(name, help, default, validator, converter, value, help_group))

    def BoolVariable(self, name, help, default, value=None, help_group=None):
        self.vars.Add(Variables.BoolVariable(name, help, default, value, help_group))

    def IntVariable(self, name, help, default, value=None, help_group=None):
        self.vars.Add(Variables.BoolVariable(name, help, default, value, help_group))

    def EnumVariable(self, name, help, default, allowed_values, map={}, ignorecase=0, value=None, help_group=None):
        self.vars.Add(Variables.EnumVariable(name, help, default, allowed_values, map, ignorecase, value, help_group))

    def ListVariable(self, name, help, default=[], names=[], map={}, value=None, help_group=None):
        self.vars.Add(Variables.ListVariable2(name, help, default, names, map, value, help_group))

    def PathVariable(self, name, help, default, validator=None, value=None, help_group=None):
        self.vars.Add(Variables.PathVariable(name, name, help, default, validator, value, help_group))

    def PackageVariable(self, name, help, default, searchfunc=None, value=None, help_group=None):
        self.vars.Add(Variables.PackageVariable(name, name, help, default, searchfunc, value, help_group))

    def ToolChain(self, name):
        return ToolChain(name)

    def Configuration(self, name, default_ver_func, post_process_func=None):
        return self.Config_Set.Configuration(default_ver_func, post_process_func)

    def __apply_tools_and_config(self, env, pre=[], post=[]):
         # apply tool chain
        env.ToolChain(pre + env['toolchain'] + post)
        # apply the configuration for the tool
        env.Configuration()

        # Get mappers
        # we apply this after the tool chain to prevent issue with
        # tools adding new mapper logic.
        mappers = self._mappers
        # set mappers
        env.Replace(**mappers)

        # this breaks up the value string toolchain in to a list of values ( need to tweak this logic when we use properties )
        env['TOOLCHAIN'] = env['toolchain'] if isinstance(env['toolchain'], str) else ",".join(
            map(lambda x: x if isinstance(x, str) else x[0] if len(x) == 1 or x[1] is None else "_".join(x), env['toolchain']))

    def DefaultEnvironment(self):
        '''
        Returns instance of the default environment for this Setting object.
        If we don't have one, we create an instance and store it in our cache.
        We would not have one, because there was a change in the Settings (which
        would remove the instance from the cache or one had not been created yet.
        '''

        # todo.. the logic for clearing the default environment has not been done yet

        key = "DefaultEnvironment"
        try:
            env = self.__env_cache[key]
        except KeyError:
            env = self._env_const_ref().Clone()
            self.__env_cache[key] = env
        return env

    def Environment(self, **kw):
        '''
        This makes a copy of environment with the toolchain and configruation set on it
        given the user is not setting tools directly. This if for Raw Scons file
        compatibilty. Otherwise we try to use any tools in our toolchain.
        '''
        return self._env_const_ref(**kw).Clone()

    def _env_const_ref(self, **kw):
        """
        This makes a reference to environment with the toolchain and configruation set on it
        given the user is not setting tools directly. This function would normally be the
        Environment() call. But we have a need to get an instance of the environment for diffing
        purposes because of this we want to pass back a instance, not a copy of the of the environment
        object, to reduce memory usage and help on the speed.

        WANRING! Clone the returned object before modifying it! This is assumed to be read only, but we have no way to enforce it
        """

        prepend = kw.get('prepend', {})
        try:
            del kw['prepend']
        except KeyError:
            pass
        append = kw.get('append', {})
        try:
            del kw['append']
        except KeyError:
            pass

        cache_key = get_cache_values(normalize_map(prepend),
                                     normalize_map(append),
                                     normalize_map(kw))  # ,
        # normalize_map(glb.defaultoverides))
        try:
            env = self.__env_cache[cache_key]
        except KeyError:
            # print "new custom"
            # check to see if the user set their own tools up in the old way
            user_tools = kw.get('tools')
            if user_tools is None:
                # we want our toolchain logic to be used
                # turn off the Scons logic for speed
                # replace['tools']=[]
                # update toolchain with a minor tweaks the user wants
                pre_tools = prepend.get('toolchain', [])
                if pre_tools != []:
                    del prepend['toolchain']
                post_tools = append.get('toolchain', [])
                if post_tools != []:
                    del append['toolchain']
                # minor messing around with tools still need
                # some tools I would not view as "tools"
                # that would be part of a tool chain but stuff that
                # would always exist
                post_tools.extend(['install', 'zip'])

            # get base Environment
            env = self.BasicEnvironment()
            # we need to take any values in the kw that are Variables and
            # reapply an convert logic on them. To do this we seperate them
            # from the rest of the general key values
            vars = {}
            tmp_kw = kw.copy()
            for k, v in tmp_kw.iteritems():
                # if the value if a callable we want to add it as a function
                if hasattr(v, '__call__'):
                    api.output.verbose_msgf("settings", "Adding function {0} as {1}", v, k)
                    env.AddMethod(v, k)
                if k in self.vars:
                    vars[k] = v
                    del kw[k]

            # Clone it and apply any overides we need to.
            env = env.Clone(**kw)

            # reapply any values that are Vars so the convert logic gets applied correctly
            for k, v in vars.iteritems():
                self.vars[k].Update(env, v)

            # apply our tool chain user is not using a hard coded SCons one
            if user_tools is None:
                self.__apply_tools_and_config(env, pre_tools, post_tools)

            # append any data or prepend any data as needed
            # will probally need better error handling later
            for k, v in append.iteritems():
                has_hey = k in env
                if util.isList(v) and has_hey:
                    env.AppendUnique(**{k: v})
                elif util.isList(v) and not has_hey:
                    env[k] = v
                else:
                    api.output.warning_msg('Ignoring appending value', k, "as it is not a list. It is type", type(v), ".")

            for k, v in prepend.iteritems():
                has_hey = k in env
                if util.isList(v) and has_hey:
                    env.PrependUnique(**{k: v})
                elif util.isList(v) and not has_hey:
                    env[k] = v
                else:
                    api.output.warning_msg('Ignoring prepending value', k, "as it is not a list. It is type", type(v), ".")

            self.__env_cache[cache_key] = env

        # See if the user want to whack the default environment with the shell value.
        if SCons.Script.GetOption('use_env') == True:  # or self.UseSystemEnvironment:
            env['ENV'] = os.environ
        return env

    def BasicEnvironment(self, toolpath=[]):
        '''
        This makes a minimum environment with no tool or configuration setup,
        but has all "parts" variables done. This does not allow for any overides
        it is as it says here.. it is a basic environment based on the Setting
        object values
        '''

        try:
            env = self.__env_cache["base"]
        except KeyError:
            env = self._basic_base_env(tools=[], **{'toolpath': toolpath})
            # apply variable values
            # get command line args
            # these are first priority overides
            overrides = copy.deepcopy(SCons.Script.ARGUMENTS)
            # get set of config files to process
            # these are second priority overides
            cfg_files = [SCons.Script.GetOption('cfg_file')]
            # get global overrides is any
            # these are third priority overides
            glb_defaults = {}  # Don't have any at the moment. review for later removal, once setting is public
            # apply values
            self.vars.Update(env, args=overrides, files=cfg_files, user_defaults=glb_defaults, add_unknown=True)

            # get the builders
            builders = self._builders
            # set builders
            env['BUILDERS'].update(builders)

            # stuff to zap.. backwards compatiblity
            env["ARCHITECTURE"] = deprecated("ARCHITECTURE", "TARGET_ARCH", env['TARGET_ARCH'])
            env["config"] = deprecated("config", "CONFIG", env['CONFIG'])

            self.__env_cache["base"] = env
        return env.Clone()

    def _handle_var_change(self):
        # if self.__env_cache!={}:
        #    print "Cleared Cache"
        self.__env_cache = {}

    @property
    def _mappers(self):
        return glb.mappers

    @property
    def _builders(self):
        return glb.builders

#########

    #@cache
    def _basic_base_env(self, **kw):
        '''
        This creates a base environment with the mininium stuff needed
        Deal with mostly, internal hacks or system tweaks. BasicEnvironment()
        deals with common general case.
        '''

        # create a new environment
        # get our toolpath if it not set by the user
        try:
            tool_path = common.make_list(kw['toolpath'])
            del kw['toolpath']
        except:
            tool_path = []
        # add the Parts toolpaths
        tool_path += load_module.get_site_directories('tools')

        # add extra value we have
        kw["PARTS_MODE"] = glb.engine._build_mode

        # make the SCons environment #############################
        env = SCons.Script.Environment(
            toolpath=tool_path,
            **kw
        )

        env['HOST_PLATFORM'] = glb._host_sys
        env['_BUILD_CONTEXT_FILES'] = set()  # make a Var

        # some general values we need to setup on any given system
        env['PART_USER'] = common.GetUserName(env)
        env['RPATH'] = []  # double check this case, linker tools may have this covered now.

        # some setup we want in the "shell" Environment

        if env['HOST_PLATFORM']['OS'] == 'win32':
            # add certain paths for windows, that have been missing.
            env.AppendENVPath('PATH', SCons.Platform.win32.get_system_root(), delete_existing=1)
            env.AppendENVPath('PATH', SCons.Platform.win32.get_system_root() + '\\system32', delete_existing=1)
            env['ENV']['USERNAME'] = env['PART_USER']

        elif env['HOST_PLATFORM'] == 'posix':
            env['ENV']['HOME'] = os.environ['HOME']
            env['ENV']['USER'] = env['PART_USER']

        # add path to current Python being used, so we use this instead of some other version
        # this allow Command that run python to work as expected
        env.PrependENVPath('PATH', os.path.split(sys.executable)[0], delete_existing=True)

        # return the cached env
        return env

    def Component(self,):
        return self.Part()

    def Part(self):
        return Part_t(config_content=self,)

    def __has_env_cached():
        ''' tells is the current state of this configuration object has a cached
        environment created yet.
        '''


def DefaultSettings():
    try:
        return DefaultSettings.__cache
    except AttributeError:
        DefaultSettings.__cache = Settings()
        return DefaultSettings.__cache
