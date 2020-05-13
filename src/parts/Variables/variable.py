


import types

import parts.api as api
import parts.events as events
import SCons.Environment
import SCons.Util
from SCons.Debug import logInstanceCreation

# remove to use common version once we clean up code a bit more


def make_list(obj):
    '''
    The purpose of thsi function is to make the obj into a list if it is not
    already one. It will flatten as well
    '''
    if SCons.Util.is_List(obj):
        return SCons.Util.flatten(obj)
    return [obj]


class Variable:

    def __init__(self, name, help=None, default=None, validator=None, converter=None, value=None, help_group=None):
        if __debug__:
            logInstanceCreation(self)
        if SCons.Util.is_List(name) or SCons.Util.is_Tuple(name):
            for k in name:
                if not SCons.Util.is_String(k) or \
                        not SCons.Environment.is_valid_construction_var(k):
                    api.output.error_msg("Illegal Variables.Add() key {0}".format(str(k)))
            self.__name = name[0]
            self.__aliases = name[1:]
        else:
            if not SCons.Util.is_String(name) or \
                    not SCons.Environment.is_valid_construction_var(name):
                api.output.error_msg("Illegal Variables.Add() key {0}".format(str(name)))
            self.__name = name
            self.__aliases = []

        self.__converter = converter
        self.__validator = validator
        self.__default = default

        self.__value = value

        self.__helpstr = help
        self.__help_group = help_group

        self._on_change = events.Event()
        self.__env = None

    def _changeable(self, obj):
        # if it is one of these guys we feel that
        # it should be inmutable from our point of view
        # may need some tweaking still
        if isinstance(obj, int) or\
                isinstance(obj, bool) or\
                isinstance(obj, float) or\
                isinstance(obj, complex) or\
                isinstance(obj, str) or\
                isinstance(obj, types.LambdaType) or \
                isinstance(obj, types.MethodType) or \
                isinstance(obj, types.ModuleType) or \
                isinstance(obj, types.CodeType):
            return False
        return True

    @property
    def Aliases(self):
        return self.__aliases

    @property
    def Value(self):
        if self.__value is None:
            return self.Default
        if self._changeable(self.__value):
            # it is possible this could be changed outside our knowledge
            # because of this we say that it changed
            self._on_change()
        return self.__value

    @Value.setter
    def Value(self, value):
        self.__value = value
        self._on_change()

    def isValid(self, env):
        if self.__env is None:
            env = DefaultEnvironment()
        else:
            env = self.__env

        try:
            self.Update(env.Clone())
        except Exception:
            return False

        return True

    def Update(self, env, value=None):
        '''Updates the environment with the value after converting it and validating it

        @param env The Scons environment to update
        @param value Optional value to update this Variable Value with given that it not already set manual overide
        '''
        # set up the value we will set
        if value is None:
            value = self.Value
        elif self.__value is None:
            value = self.__value = value
        # set the value
        env[self.__name] = value
        # convert the value
        if self.__converter:
            str_value = env.subst('${{{0}}}'.format(self.__name))
            try:
                try:
                    env[self.__name] = self.__converter(str_val=str_value, raw_val=value)
                except TypeError:
                    try:
                        env[self.__name] = self.__converter(str_value, env)
                    except TypeError:
                        env[self.__name] = self.__converter(str_value)
            except ValueError as x:
                raise SCons.Errors.UserError('Error converting option: %s\n%s' % (self.__name, x))
        # validate the value
        if self.__validator:
            str_value = env.subst('${{{0}}}'.format(self.__name))
            self.__validator(self.__name, str_value, env)

    @property
    def Name(self):
        return self.__name

    @property
    def Default(self):
        if self._changeable(self.__value):
            # it is possible this could be changed outside our knowledge
            # because of this we say that it changed
            self._on_change()
        return self.__default

    @Default.setter
    def Default(self, value):
        self.__default = value
        self._on_change()

    @property
    def Validator(self):
        return self.__validator

    @Validator.setter
    def Validator(self, value):
        self.__validator = value

    @property
    def Converter(self):
        return self.__converter

    @Converter.setter
    def Converter(self, value):
        self.__converter = value

    @property
    def Help(self):
        return self.__help

    @Validator.setter
    def Help(self, value):
        self.__help = value

    @property
    def HelpGroup(self):
        return self.__help_group

    @Converter.setter
    def HelpGroup(self, value):
        self.__help_group = value

    def __str__(self):
        return str(self.Value)
