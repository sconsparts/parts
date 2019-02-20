'''
Module contains overrides for SCons.Debug module
'''
from __future__ import absolute_import, division, print_function

import weakref

import SCons.Debug
import SCons.Script


def wrap_logInstanceCreation(func):
    '''
    Setup SCons.Debug.logInstanceCreation function overriding.

    Current created instance tracking algorithm does not remove
    destroyed instances from the list. We want to implement such functionality.
    SCons uses dict of list objects to track the instances. We use dict of set objects.
    This allows us to remove objects faster.

    Since the function is used via 'from ... import ...' statement
    we cannot just replace reference to it in a singe module.
    We override the function code object instead.
    '''
    try:
        tracked_classes = func.__globals__['tracked_classes']
    except KeyError:
        return

    if not 'count' in (SCons.Script.GetOption('debug') or []):
        # To save memory we will count objects only when we are asked for.
        def empty(instance, name=None):
            pass
        func.__code__ = empty.__code__
        tracked_classes.clear()
        return

    class wref(weakref.ref):
        '''
        Class of objects to keep references to counted objects.
        '''

        def __hash__(self): return id(self)
        '''
        We override hash function to allow count non-hashable objects.
        '''

    def remover(list_instance):
        '''
        This function will be called when counted object is destroyed.
        '''
        def remove(x):
            try:
                list_instance.remove(x)
            except BaseException:
                pass
        return remove

    # When wrap_logInstanceCreation is called there are some entries in the tracked_classes already.
    # Convert the lists to sets.
    for key, refs in list(tracked_classes.items()):
        tracked_classes[key] = the_set = set()
        the_set.update(wref(ref(), remover(the_set)) for ref in refs if ref() is not None)

    func.__globals__.update(
        wref=wref,
        remover=remover
    )

    def logInstanceCreation(instance, name=None):
        global tracked_classes
        global remover
        global wref
        if name is None:
            name = '.'.join((instance.__class__.__module__, instance.__class__.__name__))
        if name not in tracked_classes:
            tracked_classes[name] = the_set = set()
        else:
            the_set = tracked_classes[name]
        the_set.add(wref(instance, remover(the_set)))

    func.__code__ = logInstanceCreation.__code__


wrap_logInstanceCreation(SCons.Debug.logInstanceCreation)

# vim: set et ts=4 sw=4 ai :
