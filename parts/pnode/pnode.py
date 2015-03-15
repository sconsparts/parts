
from .. import glb
from .. import errors

from SCons.Debug import logInstanceCreation

class pnode(object):
    """description of class"""
    __slots__=[
        # Some internal magic
        '__weakref__',

        '__load_state',
        '_remove_cache',
        '__is_loading',
        '_isVisited'
    ]
    def __init__(self):
        if __debug__: logInstanceCreation(self)
        self.__load_state=glb.load_none
        self._remove_cache=False
        # state
        self.__is_loading=False
        self._isVisited=False

    @property
    def LoadState(self):
        ''' This get the LoadState, or the state in which this node has been loaded so far
        values can be None,Cache and File
        '''
        return self.__load_state

    @LoadState.setter
    def LoadState(self,value):
        ''' This sets the LoadState, or the state in which this node has been loaded so far
        values can be None,Cache and File
        '''
        self.__load_state=value

    @property
    def isLoading(self):
        ''' Tell us if we are being loaded
        '''
        return self.__is_loading

    @isLoading.setter
    def isLoading(self,value):
        ''' Tell us if we are being loaded
        '''
        self.__is_loading=value

    @property
    def Stored(self):
        try:
            return self.LoadStoredInfo()
        except errors.LoadStoredError:
            return None

    def LoadStoredInfo(self):
        raise NotImplementedError

    def StoreStoredInfo(self):
        raise NotImplementedError

    def GenerateStoredInfo(self):
        raise NotImplementedError

    @property
    def ID(self):
        raise NotImplementedError

    @property
    def isVisited(self):
        return self._isVisited

    @isVisited.setter
    def _set_isVisited(self,value):
        self._isVisited=value

    def __repr__(self):
        return "<{1} object at 0x{2:x} ID={3}>".format(self.__module__,self.__class__.__name__,id(self),self.ID)


def pnode_factory(klass,*lst,**kw):
    '''Default factory logic for Pnode types'''

    # from input figure out the ID to get the node
    # and if we need to setup the node with passed in data
    id,setup=klass._process_arg(*lst,**kw)
    if id and setup and glb.pnodes.isKnownPNode(id):
        # we have the node .. Get it
        ret= glb.pnodes.GetPNode(id)
        if ret.LoadState ==glb.load_cache and ret.ReadState ==glb.load_file:
            # this is a case of promotion from a cache to file load state
            # when this happens we want to regenerate the node
            ret.__init__(*lst,**kw)
            ret.LoadState=glb.load_cache
        # setup the node
        ret._setup_(*lst,**kw)

    elif id and setup and not glb.pnodes.isKnownPNode(id):
        #We don't have this node yet
        #make it
        ret= klass(*lst,**kw)
        # setup the node
        ret._setup_(*lst,**kw)
        # register it
        glb.pnodes.AddPNodeToKnown(ret)
    elif id and not setup and glb.pnodes.isKnownPNode(id):
        # we have the node .. Get it
        ret= glb.pnodes.GetPNode(id)
    elif id and not setup and not glb.pnodes.isKnownPNode(id):
        #We don't have this node yet
        #make it
        ret= klass(*lst,**kw)
        # register it
        glb.pnodes.AddPNodeToKnown(ret)
    elif not id:
        # can not generate the ID at this point
        # but this does not mean we don't have
        # an instance of this object
        # so we make a tmp node and call setup
        # to get an ID
        ret= klass(*lst,**kw)
        ret._setup_(gen_ID=True,*lst,**kw)
        id=ret.ID
        # see if this is a known ID
        if glb.pnodes.isKnownPNode(id):
            # This is a known node
            # get this node and return it
            ret=glb.pnodes.GetPNode(id)
            # if this known, and it is not setup
            if setup and not ret.isSetup:
                # we want to recall __init__ on the object
                # because we have new "better" init state
                ret.__init__(*lst,**kw)
            elif ret.LoadState ==glb.load_cache and ret.ReadState ==glb.load_file:
                # this is a case of promotion from a cache to file load state
                # when this happens we want to regenerate the node
                ret.__init__(*lst,**kw)
                setup=True # this should be set to True
                ret.LoadState=glb.load_cache
        else:
            # else this is not a known node
            # return the node we have and register it
            glb.pnodes.AddPNodeToKnown(ret)

        if setup and not ret.isSetup:
            # setup the node
            ret._setup_(*lst,**kw)

    return ret

# vim: set et ts=4 sw=4 ai ft=python :

