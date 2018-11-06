from __future__ import absolute_import, division, print_function

from SCons.Executor import TSList


def def_TSList___iter__(klass):
    def __iter__(self):
        return self.func().__iter__()
    klass.__iter__ = __iter__


def_TSList___iter__(TSList)

# vim: set et ts=4 sw=4 ai ft=python :
