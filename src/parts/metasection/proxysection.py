import parts.glb as glb
import parts.api.output as output
import parts.common as common
import parts.core.util as util
from parts.dependson import Component
from .metasection import MetaSection, delegate
from typing import Union, Sequence


def dependson_error(self,func):
    if func:
        output.error_msg(f"{self._metasection.Name}.DependsOn cannot be called as a decorator. Please remove the '@' symbol and try again")

class ProxySection:
    '''
    This object is what is passed to the Part file. This object contains the items we want to expose to the user.
    It store item(s) that should be processed. It does a quick check to see if there meta state saying the given callback
    should be called in this run or not. It also does a quick check to see if the callback matches expected phase name else
    raise an error.
    '''

    def __init__(self, metasection, env):
        # the meta section acts like data and definition of the Section object
        # so we create a Meta object per proxy instance
        
        self._metasection = metasection
        self._env = env

    # these are methods that exist by default for all sections from the user point of view
    def ApplyIf(self,result:bool):
        '''
        This is what the test that allow the user to say if the callback should be called
        '''
        self._metasection.GrabState()
        # if called from here we want to create the delgate object and return that with the state added to it
        if not self._metasection.States.get('_store',None):
            self._metasection.States['_store'] = result
        return lambda x: delegate(self, x)

    def Group(self, name:str):
        '''
        This set the group name of the call back to be bound with. By default the group is None.
        '''
        self._metasection.GrabState()
        # a quick validate check
        if not util.isString(name):
            output.error_msg(f"Group name can only be string type. Given was a {type(name)}")
        # if called from here we want to create the delgate object and return that with the state added to it
        if self._metasection.States.get("group",""):
            output.error_msg(f"Group '{self._metasection.States['group']}' was already defined")
        self._metasection.States['group'] = name
        return lambda x: delegate(self, x)


    def DependsOn(self, components: Union[str, Component, Sequence[Union[str , Component]]]) -> None:
        '''
        Defines a set component for this given section to depend on
        '''
        
        if self._metasection.hasStates:
            output.error_msg(f"{self._metasection.Name}.DependsOn cannot be called as a decorator. Please remove the '@' symbol and try again")

        if glb.processing_sections:
            output.error_msg("DependsOn cannot be called with a Section callback function")

        # make this a list if it is not already
        depends = common.make_list(components)

        # make any string a component object
        # add append it to known depends
        for i in depends:
            self._metasection.Depends.append(Component(self._env, i)) if util.isString(i) else self._metasection.Depends.append(i)

        return lambda x: dependson_error(self,x)
