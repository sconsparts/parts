
from typing import List, Callable


class PhaseInfo:
    def __init__(self, *, name: str, alt_names: List[str] = [], depreciated_names: List[str] = [],
     optional: bool = False, setup_func=None, requires_group:bool = False, dependson_phases:List[str]=[]): 
     #test_func: Callable[..., bool] = None):
        self.Name: str = name  # the name of the phase
        self.AltNames = alt_names # other alternate names.
        self.DepreciatedNames = depreciated_names # name that should not be used.. Will warn the user if used
        self.Optional: bool = optional # is this phase optional for a complete definition of the section
        self.SetupFunc = setup_func if setup_func else None # special function to setup arguments and call callbacks for the phase
        self.RequiresGroup = requires_group # the phase must have a defined group
        self.DependsonPhases = dependson_phases # the phase has an artificial depend on the target(s) of the dependent phase(s)

        #self.TestFunc = test_func if test_func else lambda env, *lst, **kw: self.default_test_func(env, *lst, **kw)

        # generated value for use later...
        # this allows quick mapping to phase name from any other allowed values as altname or deprecatednames.
        self.NameMap = {key:name for key in self.AltNames+self.DepreciatedNames+[self.Name]} 

