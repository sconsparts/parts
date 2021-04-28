
import types
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import parts.api as api
import parts.common as common
from parts.core.util.decorators import classproperty


def delegate(self, func, *lst, **kw):
    # test is we should register this function

    states = self._metasection.States
    self._metasection.ReleaseState()
    # if test_func(env=env, **kw) or True:

    if not states.get("_is_register") and states.get('_store', True):
        self._metasection.AddDefinePhase(func.__name__, func, states.get("group", "__nogroup__"))
        states["_is_register"] = True
    return func


class MetaSection:
    '''
    define common functions needed for the "meta" section logic

    This object is uses the Section object. It does not subclass from it.
    '''
    definition: "sectiondefinition.SectionDefinition"  # the definition to the meta sections. Used for validation logic.

    def __init__(self):
        # These are phases that have callbacks after the file is read
        # dict of phase:group:callback
        self.__definedphases: Dict[str, Dict[str, List[Callable]]] = {}
        # these are the allowed phase names

        # these are the dependent components for this sections
        self.__depends = []

        # various states we want to have during a set of delgate call to a single function
        self.__states = None
        self._state_count = 0

    @property
    def _definedphases(self):
        return self.__definedphases

    def _bind_(self, section):
        self.__section = section

    @property
    def _section(self):
        return self.__section

    @property
    def Env(self):
        return self.__section.Env

    @property
    def Part(self):
        return self.__section.Part

    def AddDefinePhase(self, name, callback, group="__nogroup__"):

        ##############################################
        # various validation checks to fail fast and ideally show the user a useful error message to allow them to
        # correct what they typed

        # validate the function name
        if name not in self.definition._namemap:
            api.output.error_msg(
                f"{name} is not an valid phase type for section '{self.Name}'\n Valid values are {list(self.definition._namemap.keys())}")

        # remap the name to the "base" name
        original_name = name
        name = self.definition._namemap[name]
        phaseinfo = self.definition.PhaseInfo(name)

        # validation check for if group is required
        if phaseinfo.RequiresGroup and group == '__nogroup__':
            api.output.error_msg(f"Phase {original_name} Must define a group. Please add a @{self.Name}.Group(<name>)")
        if callback in self.PhasesCallbacks(name):
            return

        #############################################
        # the store of the callback
        if group == "__nogroup__":
            api.output.verbose_msg(["metasection.load", "metasection"],
                                   f"Adding callback for phase {name} with function {callback}")
        else:
            api.output.verbose_msg(["metasection.load", "metasection"],
                                   f"Adding callback for phase {name} with function {callback} to group '{group}'")
        self.__definedphases.setdefault(name, {}).setdefault(group, []).append(callback)

    def isPhasesDefined(self, name: str) -> bool:
        return name in self.__definedphases

    def isPhasedGroupDefined(self, name: str, group: str = None):
        return self.isPhasesDefined(name) and group in self._definedphases[name]

    def PhasesCallbacks(self, name: str, group=None) -> List[Callable]:
        '''
        returns the set of callbacks for all the groups, a given group, or all that are not __nogroup__
        group can be:
            __nogroup__ which returns all callback not mapped to a group
            __grouped__ which returns all callback that are map to a grouped value
            None returns all callbacks
            <the group name> returns items that are mapped to that group if any
        '''
        ret = []
        if group and group != "__grouped__":
            ret = self.__definedphases.get(name, {}).get(group, [])
        elif group == "__grouped__":
            for grp, callbacks in self.__definedphases.get(name, {}).items():
                if grp != "__nogroup__":
                    ret += callbacks
        else:
            for grp, callbacks in self.__definedphases.get(name, {}).items():
                ret += callbacks

        return ret

    def DefaultPhaseSetup(self, callback, group):
        env = self.Env
        callback(env)

    def PhaseCallbackSetupFunction(self, name: str):
        '''
        get overide if provided, test that if this is a unbound meathod of this 
        class, if so make it bound, else return unbound function to be called.
        '''
        override = self.definition.PhaseInfo(name).SetupFunc
        if override and override.__globals__.get(self.__class__.__name__):
            return getattr(self, override.__name__)  # this is the bound function
        return override if override else self.DefaultPhaseSetup

    def PhaseGroups(self, phase=None) -> Set[str]:
        ''' 
        Returns all the defined groups for all phases by default
        else given a group will return all define groups for the given phase
        '''
        ret = set()
        if phase:
            ret = {group for group, callback in self.__definedphases.get(phase, {})}
        else:
            for phase, pinfo in self.__definedphases.items():
                for group, callback in pinfo.items():
                    ret.add(group)
        return ret

    def ProcessPhase(self, phase: str, group=None):
        '''
        Does basic logic of getting needed callbacks and processing them in standard way.
        This case will process all phases in the group. starting with None group
        Then does all the other in what ever order the happen to show up in
        '''

        api.output.verbose_msg(["metasection.load", "metasection"], f"Processing phase: '{phase}' group: '{group}'")
        if group:
            # these are the groups if any
            callbacks = self.PhasesCallbacks(phase, group)
        else:
            # we want a certain order here be default.
            # we process the None group first, then we process the other groups
            # in any order or in this case as they show up
            callbacks = self.PhasesCallbacks(phase, "__nogroup__")+self.PhasesCallbacks(phase, "__grouped__")
        api.output.verbose_msg(["metasection.load", "metasection"], f" {len(callbacks)} callbacks found '{callbacks}'")
        # this is the setup function
        setup_function = self.PhaseCallbackSetupFunction(phase)

        self.__section.DefiningPhase = (phase, group)
        for callback in callbacks:
            setup_function(callback, group)
        self.__section.DefiningPhase = None

    @classproperty
    def Name(cls):
        return cls.name

    @property
    def Depends(self):
        return self.__depends

    @Depends.setter
    def Depends(self, val):
        #api.output.trace_msg(["depends"], f"Adding depends to {val[0].str_sig()} to section {self.Name}")
        common.extend_if_absent(self.__depends, common.make_list(val))

    # def CreateSection(self):
    @property
    def States(self):
        if not self.__states:
            self.__states = {}
        return self.__states

    @property
    def hasStates(self):
        return self.__states is not None

    def GrabState(self):
        self._state_count += 1

    def ReleaseState(self):
        self._state_count -= 1
        if self._state_count <= 0:
            self.__states = None

    def CreateProxyType(self, phases, env):
        name = self.Name
        functions = {}  # exports

        # for phase in phases:
        # self.__phase_names.update(phase.NameMap)

        # this is called when the delegate is called
        #check_and_set_func, check_and_set_func_deprecated = def_callbacks(phase, env)

        # set the @section.phase functions
        # for name in [phase.Name] + phase.AltNames:
        #functions[name] = check_and_set_func

        # set the @section.phase functions
        # for name in phase.DepreciatedNames:
        #functions[name] = check_and_set_func_deprecated

        def call(self, func=None):
            # check the we have state defined in meta section

            # get the state just to make sure we have one
            self._metasection.States
            self._metasection.GrabState()

            # current limit this to a function or bool type
            if isinstance(func, types.FunctionType):
                return delegate(self, func)
            elif isinstance(func, bool):
                self._metasection._state_count -= 1  # a little hackery
                return self.ApplyIf(func)
            else:
                api.output.error_msg("Inputs can only be a bool from a condition test")

                # set the @section def phase() functions
        functions['__call__'] = call

        # set the @section function
        #functions[name] = check_and_set_class
        from .proxysection import ProxySection

        # return ProxySection.__class__(f'{self.name}ProxyType', (ProxySection,), functions)
        return type(f'{self.name}ProxyType', (ProxySection,), functions)
