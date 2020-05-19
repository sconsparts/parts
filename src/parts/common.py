###########
# Common code and general objects
##########



import fnmatch
import getpass
import imp
import os
import string
import sys
import types
from builtins import range

import parts.core.util as util
import parts.glb as glb
import SCons.Errors
# import Scons stuff
import SCons.Script
import SCons.Tool
import SCons.Util
from SCons.Debug import logInstanceCreation


def GetUserName(env):
    '''get the current username on the system'''
    return env.get('PART_USER', getpass.getuser())

###############
# this class allows us to add object varible that get a reference to the env
# that holds it


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

        def tmp(): return sfmt.format(*lst, **kw)
        super(dformat, self).__init__(tmp)


class namespace(dict, bindable):
    ''' helper class to allow making subst varaible in SCons to allow a clean
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
        if (util.isString(tmp) or tmp is None) and 'env' in self.__dict__:
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
        Howevere I have updated the overrides to handle the clone of objects
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


def process_tool_arg(lst):
    tmplst = []
    for i in lst:
        if util.isString(i):
            tmp = i.split('_', 2)
        else:
            tmp = i
        if len(tmp) == 1:
            tmp.append(None)
        elif len(tmp) != 2:
            # error
            print("Invalid tool defined [", tmp, ']')
            Exit(1)
        elif tmp[1] == '':
            tmp[1] = None
        tmplst.append(tmp)
    tmplst.reverse()
    return tmplst


def get_content(obj):
    ret = None
    # Is this a function?
    if isinstance(obj, types.LambdaType) or \
            isinstance(obj, types.MethodType) or \
            isinstance(obj, types.FunctionType) or\
            isinstance(obj, types.CodeType):
        return SCons.Action._object_contents(obj)
    elif util.isDictionary(obj):
        ret = '{'
        # having cases in which the key are not comping in same order
        # to fix this we sort the keys as a list and iter over that
        # sorted list
        key_list = sorted(obj.keys())
        for k in key_list:
            ret += "{key}:{val},".format(key=k, val=get_content(obj[k]))
        ret += '}'
    elif util.isTuple(obj) or\
            isinstance(obj, types.GeneratorType) or\
            util.isList(obj):
        ret = '['
        for i in obj:
            ret += "{0},".format(get_content(i))
        ret += ']'
    elif util.isString(obj):
        ret = obj
    else:
        ret = str(obj)

    return ret.encode()


def matches(value, includes, excludes=None):
    '''Function help with tell if a value (as a string) matched on of the include
    patterns and doesn't match on of the exclude patterns.
    '''
    match = 0
    for pattern in includes:
        if fnmatch.fnmatchcase(value, pattern):
            match = 1
            break
    if match == 1:
        for pattern in excludes:
            if fnmatch.fnmatchcase(value, pattern):
                match = 0
                break
    return match


def make_list(obj):
    '''
    The purpose of this function is to make the obj into a list if it is not
    already one. It will flatten as well
    '''
    if util.isList(obj):
        return SCons.Util.flatten(obj)
    return [obj]


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

# For dict returns a new one by wrapping each key and value
# For list or tuple returns a new one by wrapping each item
# For function returns its name followed by wrapped arguments' list
# For instance returns class name followed by wrapped __dict__
# For class returns its name followed by wrapped __dict__
# For others returns str(obj)


def wrap_to_string(obj):
    return _wrap_to_string(obj, set())


def _wrap_to_string(obj, knownObjIds):
    if id(obj) in knownObjIds:
        return '...'

    knownObjIds.add(id(obj))
    if util.isDictionary(obj):
        return dict([[_wrap_to_string(k, knownObjIds),
                      _wrap_to_string(v, knownObjIds)] for k, v in obj.items()])
    elif util.isList(obj):
        return [_wrap_to_string(i, knownObjIds) for i in obj]
    elif isinstance(obj, tuple):
        return tuple([_wrap_to_string(i, knownObjIds) for i in obj])
    elif isinstance(obj, types.FunctionType):
        return 'function %s (%s)' % (str(obj.__name__),
                                     ','.join(_wrap_to_string(obj.__code__.co_varnames, knownObjIds)))
    elif isinstance(obj, type):
        return 'class %s %s' % (str(obj.__name__), _wrap_to_string(obj.__dict__, knownObjIds))
    else:
        return str(obj)


def is_catagory_file(env, cat, file):
    ''' this function is the master function for finding a if a file matches a type pattern.'''
    '''This function returns True if the argument looks like a file that would be copied to a LIB directory'''
    try:
        return is_catagory_file(env, cat, file.attributes.FilterAs)
    except AttributeError:
        patterns = env[cat]
        for i in patterns:
            if fnmatch.fnmatchcase(str(file), i):
                return True
        return False


def option_bool(val, option, default=False):
    if util.isString(val):
        if val.lower() == 'true':
            return True
        elif val.lower() == 'false':
            return False
        else:
            print('Parts:', option, 'set to invalid value of [', val, '], using default of value of [', default, ']')
            return default
    return bool(val)

# amazing enough python never added a relpath function....


def relpath(to_dir, from_dir=os.curdir):
    """
    Return a relative path to the target [to_dir] from either the current dir or an optional base dir(from_dir).
    Base can be a directory specified either as absolute or relative to current dir.
    Does not check to see if directories exist.. assumes you get that right yourself
    Also in drive based systems.. it returns the abs_path(to_dir) in cases of different drives
    """

    from_dir_list = (os.path.abspath(from_dir)).split(os.sep)
    to_dir_list = (os.path.abspath(to_dir)).split(os.sep)

    # On the windows platform the target may be on a completely different drive from the base.
    if os.name in ['nt', 'dos', 'os2'] and from_dir_list[0] != to_dir_list[0]:
        # we could error .. but instead I return the to_path
        return os.path.abspath(to_dir)

    # Starting from the filepath root, work out how much of the filepath is
    # shared by base and target.
    for i in range(min(len(from_dir_list), len(to_dir_list))):
        if from_dir_list[i] != to_dir_list[i]:
            break
    else:
        # If we broke out of the loop, i is pointing to the first differing path elements.
        # If we didn't break out of the loop, i is pointing to identical path elements.
        # Increment i so that in all cases it points to the first differing path elements.
        i += 1

    rel_list = [os.pardir] * (len(from_dir_list) - i) + to_dir_list[i:]
    if rel_list == []:
        return '.'
    return os.path.join(*rel_list)


# ---------------------------------------------------------------------
# parseVersionNumber
#
# Parses a version number string such as '8.1.0' and returns
# major_number, minor_number, and revision_number.  For any of these
# fields, a value of -1 means 'any'.  For example, '8.x.1' would return
# 8, -1, and 1.  The given version number string must not start with a
# product prefix.
#
# Returns (error_msg, major_number, minor_number, revision_number).
# error_msg is an empty string if there is no error.
# ---------------------------------------------------------------------
def parseVersionNumber(versionNumber):
    fields = versionNumber.split('.')
    fieldValues = [-1, -1, -1]		# default values

    for i in range(len(fields)):
        if fields[i] == 'x' or fields[i] == 'X' or fields[i] == '*':
            value = -1
        else:
            value = int(fields[i])

        fieldValues[i] = value
        # Parse only as many version numbers as we have room for
        if i + 1 == len(fieldValues):
            break

    return fieldValues[0], fieldValues[1], fieldValues[2]

# ---------------------------------------------------------------------
# CompareVersionNumbers
##
# Compares two discrete version numbers and returns (error_msg, result)
# where error_msg is an emptry string if there is no error.
# result contains the result of the comparison
# as follows:
##
# result = 0:	versionNumber1 = versionNumber2
# result < 0:	versionNumber1 < versionNumber2
# result > 0: versionNumber1 > versionNumber2
##
# Arguments must be in the discrete version string format, e.g. '8.1.2'.
# Argument of None is considered to be less than '0.0.0'
##
# Returns (error_message, result) where error_message is '' if no error.
# ---------------------------------------------------------------------
# def CompareVersionNumbers(verStr1, verStr2):
#    if verStr1 == None and verStr2 == None:
#        return 0
#
#    if verStr1 == None and verStr2 != None:
#        return -1
#
#    if verStr1 != None and verStr2 == None:
#        return 1
#
#    major1, minor1, rev1 = parseVersionNumber(verStr1)
#
#    major2, minor2, rev2 = parseVersionNumber(verStr2)
#
#    if major1 < major2 and not (major1 == -1 or major2 == -1):
#        return -1
#    if major1 > major2 and not (major1 == -1 or major2 == -1):
#        return 1
#
#    if minor1 < minor2 and not (minor1 == -1 or minor2 == -1):
#        return -1
#    if minor1 > minor2 and not (minor1 == -1 or minor2 == -1):
#        return 1
#
#    if rev1 < rev2 and not (rev1 == -1 or rev2 == -1):
#        return -1
#    if rev1 > rev2 and not (rev1 == -1 or rev2 == -1):
#        return 1
#
#    return 0


# help objects
class _make_rel:

    def __init__(self, lst):
        if __debug__:
            logInstanceCreation(self)
        self.lst = lst

    def string_it(self, env, path):
        import pattern
        ret = '[ '
        for i in self.lst:
            if isinstance(i, SCons.Node.FS.Dir):
                ret += "env.Dir('" + relpath(env.Dir(i).srcnode().abspath, path) + "')"
            elif isinstance(i, pattern.Pattern):
                _, sr = i.target_source(path)
                inc = []
                for s in sr:
                    inc.append(relpath(s, path).replace('\\', '/'))
                # installed_files+=env.InstallAs(t,sr)
                s = 'Pattern(src_dir="' + relpath(i.src_dir.abspath, path).replace('\\', '/') + '",includes = ' + str(inc)
                if i.sub_dir != '':
                    s += ",sub_dir='" + str(i.sub_dir) + "'"
                s += ")"
                ret += s
            else:
                ret += "'" + relpath(env.File(i).srcnode().abspath, path).replace('\\', '/') + "'"
            ret += ','
        ret = ret[:-1] + ']'
        return ret


class _make_reld:

    def __init__(self, lst):
        if __debug__:
            logInstanceCreation(self)
        self.lst = lst

    def string_it(self, env, path):
        ret = []
        for i in self.lst:
            if isinstance(i, SCons.Node.FS.Dir):
                ret.append("env.Dir(" + relpath(env.Dir(i).srcnode().abspath, path) + ")")
            else:
                ret.append(relpath(env.Dir(i).srcnode().abspath, path))
        return str(ret)


class named_parms:

    def __init__(self, _kw):
        if __debug__:
            logInstanceCreation(self)
        self.kw = _kw

    def string_it(self, env, path):
        ret = ""
        i = len(self.kw)
        for k, v in self.kw.items():
            i = i - 1
            ret += str(k) + "=" + gen_arg(env, path, v)
            if i > 0:
                ret += ','
        if ret == '':
            ret = '**{}'
        return ret


def gen_arg(env, sdk_path, value):
    ret = ''
    if isinstance(value, _make_rel):
        ret += value.string_it(env, sdk_path)
    elif isinstance(value, _make_reld):
        ret += value.string_it(env, sdk_path)
    elif isinstance(value, named_parms):
        ret += value.string_it(env, sdk_path)
    elif util.isString(value):
        ret += "'" + env.subst(value) + "'"
    else:
        ret += str(value)
    return ret


def func_gen(env, sdk_path, func, values):
    s = '    env.' + func + '('
    i = len(values)
    for v in values:
        i = i - 1
        s += gen_arg(env, sdk_path, v)
        if i > 0:
            s += ','
    s += ')'
    return s


def map_alias_to_root(pobj, concept, alias_str):
    '''
    Returns a list of Alias nodes.
    Each successor is predecessor's parent. I.e. [node, node.parent, node.parent.parent, ...]
    '''

    alias_str = alias_str.format(concept, "${ALIAS}")
    alias = pobj.Env.Alias(alias_str)

    result = list(alias)
    while pobj.Parent:
        pobj = pobj.Parent
        alias = pobj.Env.Alias(alias_str, alias)
        result.extend(alias)

    return result

# vim: set et ts=4 sw=4 ai ft=python :
