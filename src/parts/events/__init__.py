from __future__ import absolute_import, division, print_function

from SCons.Debug import logInstanceCreation

# simple event class
# need to look at extending this or
# finding a usable existing solution


class Event(object):

    def __init__(self):
        if __debug__:
            logInstanceCreation(self)
        self.__callbacks = list()

    def Connect(self, callback):
        self.__callbacks.append(callback)
        return self

    def __iadd__(self, callback):
        return self.Connect(callback)

    def Disconnect(self, callback):
        try:
            self.__callbacks.remove(callback)
        except Exception:
            pass
        return self

    def __isub__(self, callback):
        return self.Disconnect(callback)

    def __call__(self, *args, **kargs):
        for callback in self.__callbacks:
            callback(*args, **kargs)

    def __len__(self):
        return len(self.__callbacks)
