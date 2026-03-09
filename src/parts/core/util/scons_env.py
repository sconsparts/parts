from SCons.Debug import logInstanceCreation

from .is_a import isString


class bindable:

    def _bind(self, env, key):
        raise NotImplementedError

    def _rebind(self, env, key):
        raise NotImplementedError


class DelayVariable:
    ''' This class defines a varable that will not be evaluted until it is requested
    This allow it to be assigned some logic and not execute it till requested, as needed
    The class will reset the value in the SCons Environment with the delayed value
    once it is evaluated
    '''
    __slots__ = ['__func']

    def __init__(self, func):
        if __debug__:
            logInstanceCreation(self)
        self.__func = func

    def __eval__(self):
        return self.__func()

    def __str__(self):
        return str(self.__eval__())

    def __repr__(self):
        return str(self.__eval__())

    def __getitem__(self, key):
        return self.__func()[key]


class dformat(DelayVariable):

    def __init__(self, sfmt, *lst, **kw):
        if __debug__:
            logInstanceCreation(self)

        def tmp():
            return sfmt.format(*lst, **kw) if kw or lst else sfmt

        super().__init__(tmp)


class namespace(dict, bindable):
    ''' helper class to allow making subst variable in SCons to allow a clean
    form of $a.b
    '''

    def __init__(self, **kw):
        if __debug__:
            logInstanceCreation(self)
        dict.__init__(self, kw)

    def __getattr__(self, name):
        ''' This is ugly but because SCons does not have a good recursive subst
        code, I need to subst stuff here before SCons can try to, else it will
        try to set this object to Null string, causing an unwanted error'''
        try:
            tmp = self[name]
        except KeyError:
            raise AttributeError()
        if hasattr(tmp, '__eval__'):
            tmp = tmp.__eval__()
            self[name] = tmp
        if (isString(tmp) or tmp is None) and 'env' in self.__dict__:
            return self.env.subst(tmp)
        return tmp

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        del self[name]

    def _rebind(self, env, key):
        '''
        Rebind the environment to a new one.
        There does not seem a way to have this happen in a clone
        as from what I can see semi_deep_copy does not pass a new env
        However I have updated the overrides to handle the clone of objects
        that are bindable to the env to be cloned and handled better.
        '''
        tmp = namespace(**self.copy())
        tmp._bind(env, key)
        return tmp

    def _bind(self, env, key):
        self.__dict__['env'] = env

    def clone(self):
        tmp = namespace(**self.copy())
        tmp._bind(None, None)
        return tmp

# vim: set et ts=4 sw=4 ai ft=python :
