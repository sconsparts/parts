
import parts.api as api
from parts.pnode.nilsection import NilSection
import SCons.Executor

class NilPart:
    ''' 
    This class acts as an empty shim for cases when we have optional depends
    '''

    def __init__(self):
        pass
    
    @property
    def Env(self) -> dict:
        return SCons.Executor.get_NullEnvironment()
    
    def Section(self, case:str) -> NilSection:
        api.output.trace_msg("nilpart",f"Section called with case:{case}")
        return NilSection()


