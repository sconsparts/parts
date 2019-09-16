
from __future__ import absolute_import, division, print_function

import os
import sys

import parts.common as common
import parts.api as api
import parts.events as events
import SCons.Environment
import SCons.Util
from parts.common import make_list
from SCons.Debug import logInstanceCreation

from .variable import Variable


class Variables(dict, object):
    ''' Container of variable we will want to add to a given Environment.
    The object allow for setting and getting of variable before the Environment is created.
    It will also define convert and valiade and value before it is set

    '''
# __slots__=[
# '__args',
# '__files'
# '__user_defaults',
# '__unknowns'
# ]

    def __init__(self, files=None, args=None, user_defaults=None, **kw):
        """
        Construct a Varibles object

        @param files List of optional configuration files to load
        @param args The command line ARGUMENTS used to override any value from the command line
        @param user_defaults Values to overide the defined varaible defaults with
        """
        if __debug__:
            logInstanceCreation(self)

        if args is None:
            args = {}
        self.__dict__['_args'] = args
        if files is None:
            files = []
        self.__dict__['_files'] = make_list(files)
        if user_defaults is None:
            user_defaults = {}
        self.__dict__['_user_defaults'] = user_defaults
        # Value that we get added via loading data from the CLI arguments or
        #  cfg files that are not defined aleady
        self.__dict__['_unknowns'] = {}
        self.__dict__['_on_change'] = events.Event()

        for k, v in kw.items():
            if not isinstance(v, Variable):
                kw[k] = Variable(v)
            kw[k]._on_change += self._on_change

        dict.__init__(self, kw)

    @property
    def Files(self):
        return self._files

    @Files.setter
    def Files(self, lst):
        self._files = make_list(lst)

    def __getattr__(self, name):
        ''' Used for dynamic access of variable by the user
        @param name The name of variable we want to access. If it does not exist a KeyError will be raised
        '''
        tmp = self[name]
        return tmp

    def __setattr__(self, name, value):
        '''Used for dynamic setting of variable value by the user

        @param name The name of variable we want to access. If it does not exist a KeyError will be raised
        @param value The value we want to set. See notes below.

        This function makes sure everything is a Variable class type. It will only truly replace if this value is of a Variable type,
        otherwise it replaces the value of an exist Variable or it will wrap that value in a Generic Varible object'''
        if name in self.__dict__:
            self.__dict__[name] = value
        elif isinstance(value, Variable):
            self[name] = value
        elif name in self:
            self[name].value = value
        else:
            self[name] = Variable(name, value=value)
            self[name]._on_change += self._on_change
            self._on_change()

    def __setitem__(self, name, value):
        if isinstance(value, Variable):
            dict.__setitem__(self, name, value)
        elif name in self:
            self[name].value = value
        else:
            value = Variable(name, value=value)
            dict.__setitem__(self, name, value)
            self[name]._on_change += self._on_change
            self._on_change()

    def __delattr__(self, name):
        del self[name]

    def AddVariables(self, *optlist):
        """
        Add a list of options.

        Each list element is a tuple/list of arguments to be passed on
        to the underlying method for adding options.

        Example:
          opt.AddVariables(
            ('debug', '', 0),
            ('CC', 'The C compiler'),
            ('VALIDATE', 'An option for testing validation', 'notset',
             validator, None),
            )
        """
        for o in optlist:
            if isinstance(o, Variable):
                # new case
                self.Add(o)
            else:
                # classic case
                self.Add(*o)

    def Add(self, key, help=None, default=None, validator=None, converter=None, help_group=None, **kw):
        '''This will add a Variable that will the user can overide on the Command like or with a config file
        @param key The name of the varable to add, or is a varaible type, if the latter the other arguments as overides
        @param help The help text for this given item
        @param default The default value to be used for the variable, if no other value is provided.
        @param validator An optional call back function that will validate the value as good or bad
        @param converter An optional function used to convert and set the value in the Environment, if not provided a default one is used
        @param **kw is ignored at this time

        This function exist as a backward compatibility function.. normally the Setting.XXXVariable() api would be called
        '''
        if isinstance(key, Variable):
            if help:
                key.Help = help
            if default:
                key.Default = default
            if validator:
                key.Validator = validator
            if converter:
                key.Converter = converter
            if help_group:
                key.HelpGroup = help_group
            val = key
            key = val.Name
        else:
            val = Variable(key,
                           help=help,
                           default=default,
                           validator=validator,
                           converter=converter,
                           help_group=help_group)
            if SCons.Util.is_List(key) or SCons.Util.is_Tuple(key):
                key = key[0]
        if key in self:
            api.output.warning_msg("Variable {0} is already defined.".format(key))
        val._on_change += self._on_change
        self[key] = val

    def Update(self, env, args=None, files=None, user_defaults=None, add_unknown=False):
        """
        Update an environment with the option variables.

        @param env the Environment to update
        @param args The command line arguments, or top level dictionary of key values that have top priority
        @param files A list of files to load, have second priority
        @param user_default A dictionary of Key value pair that overide any default values, has third priority
        @param add_unknowns If True values passed in Keys that are in args, files, defaults that don't have a defined varible will be added to the environment.
        """

        # this is the dict with the final values
        values = {}
        if user_defaults is None:
            user_defaults = self._user_defaults

        # user overides to default values
        # first fill in all options value with default values
        for k, option in self.items():
            # if not option.default is None:
            values[k] = option.Default
        # add any default overides
        values.update(user_defaults)

        # File overides
        # next set the value specified in the options file
        # keep as SCons has it orginally
        if files is None:
            files = self._files
        for filename in files:
            if filename is None:
                break
            if os.path.exists(filename):
                dir = os.path.split(os.path.abspath(filename))[0]
                if dir:
                    common.prepend_unique(sys.path, dir)
                try:
                    values['__name__'] = filename
                    with open(filename) as file_obj:
                        file_content = file_obj.read()
                    exec(file_content.replace('\r', '\n'), {}, values)
                finally:
                    # cleanup
                    if dir:
                        del sys.path[0]
                    del values['__name__']

        # any commandline arguments/user added values
        # set the values specified on the command line
        # if None, SCons is not passing any to us
        if args is None:
            # use the user supplied arguments, if this is the case
            args = self._args

        # Override any value we have with Arguments provided
        for arg, value in args.items():
            # we need to see if there is a alias for this
            # for each option we need to test if this is an alias+key that
            # is a match for the arg
            for k, option in self.items():
                if arg in option.Aliases + [k]:
                    # we have a match, so store and break for this argument
                    values[k] = value
                    break
            else:
                # no match was found so we store this in unknowns
                self._unknowns[arg] = value

        # at this point the values should be up to date
        # put the variables in the environment:
        to_remove = []
        for k, v in values.items():
            # There is a possiblility that unkown values have been read by the cfg file
            # This code will try to get the option and if that fails adds it to the unknowns
            tmp = self.get(k, None)
            if tmp:
                env[k] = v
            else:
                self._unknowns[k] = v
                to_remove.append(k)
        for k in to_remove:
            if k in values:
                del values[k]
        if add_unknown:
            env.Replace(**self._unknowns)
        # this loop allow the convertion and validation
        for k, v in values.items():
            tmp = self[k]
            tmp.Update(env, v)

    def UnknownVariables(self):
        """
        Returns any options in the specified arguments lists that
        were not known, declared options in this object.
        """
        return self._unknowns

    def Save(self, filename, env):
        pass

    def GenerateHelpText(self, env, sort=None):
        return "to do"

    format = '\n%s: %s\n    default: %s\n    actual: %s\n'
    format_ = '\n%s: %s\n    default: %s\n    actual: %s\n    aliases: %s\n'

    def FormatVariableHelpText(self, env, key, help, default, actual, aliases=[]):
        pass


# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
