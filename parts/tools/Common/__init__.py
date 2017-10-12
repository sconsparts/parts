from SCons.Subst import quote_spaces
from SCons.Subst import CmdStringHolder


class toolvar(str, CmdStringHolder):
    '''
        toolvar should look like str to be passed to os.open/os.stat etc.
        toolvar should look like CmdStringHolder to be correctly quoted 
    '''
    literal = False
    '''
    Tool var has to have literal property to look like CmdStringHolder
    '''
    def __new__(cls, command, type_list=None, env=None):
        if env and not env.get('PARTS_USE_SHORT_TOOL_NAMES'):
            command = str(env.WhereIs(command) or command)
        return super(toolvar, cls).__new__(cls, command)

    def __init__(self, command, type_list=None, env=None):
        self.__tlist = frozenset(type_list or ())

    def __eq__(self, val):
        return super(toolvar, self).__eq__(val) or val in self.__tlist

    def __ne__(self, val):
        return not self.__eq__(val)

    @property
    def data(self):
        '''
        Tool var has to have data property to look like CmdStringHolder
        '''
        return str(self)

# vim: set et ts=4 sw=4 ai ft=python :
