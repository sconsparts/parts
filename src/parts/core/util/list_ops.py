from typing import Sequence, TypeVar, Union, List

import SCons.Util

from .is_a import isList

T = TypeVar('T')


def make_list(obj: Union[T, Sequence[T]]) -> List[T]:
    '''
    The purpose of this function is to make the obj into a list if it is not
    already one. It will flatten as well
    '''
    if not isList(obj):
        obj = [obj]
    return SCons.Util.flatten(obj)


def make_unique(obj):
    ''' The purpose of this object is to make a list
    with only unique values in it.
    The input is the list object.
    It returns the new list (Note this is NOT a deep copy)
    [a,b,c,b]-> [a,b,c]
    '''
    tmp = []
    for i in obj:
        if not i in tmp:
            tmp.append(i)
    return tmp


def extend_unique(obj, lst):
    '''
    The purpose of this function is to add the items in the collection
    to a list in a unique way
    '''
    for i in lst:
        append_unique(obj, i)
    return obj


def pre_extend_unique(obj, lst):
    '''
    The purpose of this function is to add the items in the collection
    to a list in a unique way
    '''

    for i in lst:
        prepend_unique(obj, i)
    return obj


def append_unique(obj, val):
    '''
    The purpose of this function is to add the object to a list in a unique way.
    This logic here to make sure that if an item is exists twice the finial order
    is moved to the end of the list. Common logic needed for libs when linking.
    [a,b,c,b]-> [a,c,b]
    '''
    if not val in obj:
        obj.append(val)
    else:
        try:
            while True:
                obj.remove(val)
        except ValueError:
            pass
        obj.append(val)
    return obj


def prepend_unique(obj, val):
    '''
    The purpose of this function is to add the object to a list in a unique way
    This always move an item to the front of the list if a duplicate is found
    [a,b,c,b]-> [b,c,a]
    '''
    if not val in obj:
        obj.insert(0, val)
    else:
        try:
            while True:
                obj.remove(val)
        except ValueError:
            pass
        obj.insert(0, val)

    return obj


def append_if_absent(obj, val):
    if not val in obj:
        obj.append(val)
    return obj


def extend_if_absent(obj, val):
    ''' The purpose of this function is to add to the object only the list elements which are unique'''

    for element in val:
        if element not in obj:
            obj.append(element)
    return obj


def make_unique_str(obj):
    ''' The purpose of this object is to make a list
    with only unique values in it.
    The input is the list object.
    It returns the new list (Note this is NOT a deep copy)'''
    tmp = []
    for i in obj:
        addit = True
        for j in tmp:
            if str(j) == str(i):
                addit = False
                break
        if addit:
            tmp.append(i)
    return tmp

# vim: set et ts=4 sw=4 ai ft=python :
