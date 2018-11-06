'''
This module contains overrides for SCons.Util module
'''
from __future__ import absolute_import, division, print_function

from collections import UserList

import SCons.Util
from SCons.Debug import logInstanceCreation


def def_UserList___init__(klass):
    orig = klass.__init__

    def __init__(self, *args, **kw):
        if __debug__:
            logInstanceCreation(self)
        orig(self, *args, **kw)
    klass.__init__ = __init__


#def_UserList___init__(UserList)

##from SCons.Util import UniqueList
# def def_UniqueList___iter__(klass):
# def __iter__(self):
# self._UniqueList__make_unique()
# return UserList.__iter__(self)
##    klass.__iter__ = __iter__
# def_UniqueList___iter__(UniqueList)


class UniqueList(list):

    def __init__(self, seq=[]):
        if __debug__:
            logInstanceCreation(self, 'parts.overrides.UniqueList')
        list.__init__(self, seq)
        self.unique = True

    def __hash__(self):
        return id(self)

    def __make_unique(self):
        if not self.unique:
            list = super(UniqueList, self)
            list.__setslice__(0, list.__len__(),
                              SCons.Util.uniquer_hashables(list.__getslice__(0, list.__len__())))
            self.unique = True

    def __lt__(self, other):
        self.__make_unique()
        return list.__lt__(self, other)

    def __le__(self, other):
        self.__make_unique()
        return list.__le__(self, other)

    def __eq__(self, other):
        self.__make_unique()
        return list.__eq__(self, other)

    def __ne__(self, other):
        self.__make_unique()
        return list.__ne__(self, other)

    def __gt__(self, other):
        self.__make_unique()
        return list.__gt__(self, other)

    def __ge__(self, other):
        self.__make_unique()
        return list.__ge__(self, other)

    def __cmp__(self, other):
        self.__make_unique()
        return list.__cmp__(self, other)

    def __len__(self):
        self.__make_unique()
        return list.__len__(self)

    def __getitem__(self, i):
        self.__make_unique()
        return list.__getitem__(self, i)

    def __setitem__(self, i, item):
        list.__setitem__(self, i, item)
        self.unique = False

    def __getslice__(self, i, j):
        self.__make_unique()
        return list.__getslice__(self, i, j)

    def __setslice__(self, i, j, other):
        list.__setslice__(self, i, j, other)
        self.unique = False

    def __add__(self, other):
        result = self.__class__(list.__add__(self, other))
        result.unique = False
        return result

    def __radd__(self, other):
        result = self.__class__(list.__radd__(self, other))
        result.unique = False
        return result

    def __iadd__(self, other):
        result = list.__iadd__(self, other)
        result.unique = False
        return result

    def __mul__(self, other):
        result = self.__class__(list.__mul__(self, other))
        result.unique = False
        return result

    def __rmul__(self, other):
        result = self.__class__(list.__rmul__(self, other))
        result.unique = False
        return result

    def __imul__(self, other):
        result = list.__imul__(self, other)
        result.unique = False
        return result

    def __iter__(self):
        self.__make_unique()
        return list.__iter__(self)

    def append(self, item):
        list.append(self, item)
        self.unique = False

    def insert(self, i):
        list.insert(self, i)
        self.unique = False

    def count(self, item):
        self.__make_unique()
        return list.count(self, item)

    def index(self, item):
        self.__make_unique()
        return list.index(self, item)

    def reverse(self):
        self.__make_unique()
        list.reverse(self)

    def sort(self, *args, **kwds):
        self.__make_unique()
        return list.sort(self, *args, **kwds)

    def extend(self, other):
        list.extend(self, other)
        self.unique = False


#SCons.Util.UniqueList = UniqueList


class CLVar(list):
    """A class for command-line construction variables.

    This is a list that uses Split() to split an initial string along
    white-space arguments, and similarly to split any strings that get
    added.  This allows us to Do the Right Thing with Append() and
    Prepend() (as well as straight Python foo = env['VAR'] + 'arg1
    arg2') regardless of whether a user adds a list or a string to a
    command-line construction variable.
    """

    def __init__(self, *seq):
        if __debug__:
            logInstanceCreation(self, 'parts.overrides.CLVar')
        list.__init__(self, seq and SCons.Util.Split(*seq))

    def __add__(self, other):
        result = CLVar()
        result.extend(self)
        result.extend(SCons.Util.Split(other))
        return result

    def __radd__(self, other):
        return CLVar(other).__add__(self)

    def __coerce__(self, other):
        return (self, CLVar(other))

    def __str__(self):
        return ' '.join(iter(self))

    def __getslice__(self, i, j):
        return self.__class__(list.__getslice__(self, i, j))
#SCons.Util.CLVar = CLVar

# vim: set et ts=4 sw=4 ai :
