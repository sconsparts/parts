from .metasection import MetaSection
from .phaseinfo import PhaseInfo
from .proxysection import ProxySection
from parts.core.states import GroupLogic
from typing import Sequence, Callable, Dict



class SectionDefinition:
    '''
    This class hold the definition of the a given sections.
    It will hold the meta section object and the phase info information.
    It is basically a singletome class, one per section defined
    It contains classmethods to do validation given a proxysection object
    '''
    def __init__(self, metasection: MetaSection, phaseinfo: Sequence[PhaseInfo], target_mapping_logic:GroupLogic = GroupLogic.TOP):#, exports={}):
        self.__meta_section_type: MetaSection = metasection
        self.__phases: Dict[str, PhaseInfo] = {phase.Name:phase for phase in phaseinfo}
        #self.__exports: Dict[str, Callable] = exports
        # this is used to cache the type to avoid recreating the class
        self.__proxy_type = None
        # define how we map top level target that would be defined with in a section.
        self.__target_mapping_logic = target_mapping_logic

        self._namemap = {}
        for phase in self.__phases.values():
            self._namemap.update(phase.NameMap)
        
    @property        
    def Name(self):
        return self.__meta_section_type.name

    def PhaseInfo(self, name):
        return self.__phases[name]

    @property
    def TargetMappingLogic(self) -> GroupLogic:
        return self.__target_mapping_logic
    
    def isDefined(self, proxy) -> bool:
        '''
        Returns true if the phase is defined, it may not be valid
        but there is something defined
        '''
        # the the meta data we collected
        metasection = proxy._metasection
        for phase, info in self.__phases.items():
            # do we have this phase defined
            if metasection.isPhasesDefined(info.Name):
                return True
        return False
        
    
    def isValid(self, proxy) -> bool:
        metasection = proxy._metasection
        for phase, info in self.__phases.items():
            # do we have this phase defined
            if metasection.isPhasesDefined(info.Name) or info.Optional:
                return False
        return True

    @property
    def  MetaSectionType(self):
        return self.__section_type

    def CreateProxy(self, env) -> ProxySection:        
        # create instance of MetaSection as this will hold various data items
        meta_section_t = self.__meta_section_type
        meta_section = meta_section_t()
        
        if not self.__proxy_type:
            self.__proxy_type = meta_section.CreateProxyType(self.__phases, env)
        
        return self.__proxy_type(meta_section,env)
