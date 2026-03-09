import fnmatch
import getpass
import os
import types

import SCons.Action

from .is_a import isString, isDictionary, isTuple, isList


def GetUserName(env):
    '''get the current username on the system'''
    return env.get('PART_USER', getpass.getuser())


def get_content(obj):
    ret = None
    # Is this a function?
    if isinstance(obj, types.LambdaType) or \
            isinstance(obj, types.MethodType) or \
            isinstance(obj, types.FunctionType) or\
            isinstance(obj, types.CodeType):
        return SCons.Action._object_contents(obj)
    elif isDictionary(obj):
        ret = '{'
        # having cases in which the key are not comping in same order
        # to fix this we sort the keys as a list and iter over that
        # sorted list
        key_list = sorted(obj.keys())
        for k in key_list:
            ret += "{key}:{val},".format(key=k, val=get_content(obj[k]))
        ret += '}'
    elif isTuple(obj) or\
            isinstance(obj, types.GeneratorType) or\
            isList(obj):
        ret = '['
        for i in obj:
            ret += "{0},".format(get_content(i))
        ret += ']'
    elif isString(obj):
        ret = obj
    else:
        ret = str(obj)

    return ret.encode()


def matches(value, includes, excludes=None) -> bool:
    '''Function to determine if a value (as a string) matches any of the include patterns
    and does not match any of the exclude patterns.

    Args:
        value (str): The value to be checked.
        includes (list): A list of patterns to include.
        excludes (list, optional): A list of patterns to exclude. Defaults to None.

    Returns:
        bool: True if the value matches any of the include patterns and does not match
        any of the exclude patterns, False otherwise.
    '''
    match = False
    if not includes:
        includes = ["*"]
    for pattern in includes:
        if fnmatch.fnmatchcase(value, pattern):
            match = True
            break
    if match:
        for pattern in excludes:
            if fnmatch.fnmatchcase(value, pattern):
                match = False
                break
    return match


def option_bool(val, option, default=False):
    if isString(val):
        if val.lower() == 'true':
            return True
        elif val.lower() == 'false':
            return False
        else:
            print('Parts:', option, 'set to invalid value of [', val, '], using default of value of [', default, ']')
            return default
    return bool(val)


def relpath(to_dir, from_dir=os.curdir):
    """
    Return a relative path to the target [to_dir] from either the current dir or an optional base dir(from_dir).
    Base can be a directory specified either as absolute or relative to current dir.
    Does not check to see if directories exist.. assumes you get that right yourself
    Also in drive based systems.. it returns the abs_path(to_dir) in cases of different drives

    This function is OS-independent and handles both Unix-style (/) and Windows-style (\\) paths.
    The output path separator style is detected from the input paths.
    """

    # Detect path separator style from input - prefer forward slash if present
    use_forward_slash = '/' in to_dir or '/' in from_dir

    # Normalize to forward slashes internally for consistent processing
    to_dir_norm = to_dir.replace('\\', '/')
    from_dir_norm = from_dir.replace('\\', '/')

    # Make paths absolute, then normalize separators back to forward slashes
    to_dir_abs = os.path.abspath(to_dir_norm).replace('\\', '/')
    from_dir_abs = os.path.abspath(from_dir_norm).replace('\\', '/')

    # Split using forward slash (consistent separator)
    from_dir_list = from_dir_abs.split('/')
    to_dir_list = to_dir_abs.split('/')

    # On the windows platform the target may be on a completely different drive from the base.
    if os.name in ['nt', 'dos', 'os2'] and from_dir_list[0] != to_dir_list[0]:
        # we could error .. but instead I return the to_path
        result = to_dir_abs
    else:
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

        rel_list = ['..'] * (len(from_dir_list) - i) + to_dir_list[i:]
        if rel_list == []:
            result = '.'
        else:
            result = '/'.join(rel_list)

    # Convert back to original path separator style if needed
    if not use_forward_slash and os.sep == '\\':
        result = result.replace('/', '\\')

    return result


def parseVersionNumber(versionNumber):
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


def process_tool_arg(lst):
    tmplst = []
    for i in lst:
        if isString(i):
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


def is_category_file(env, cat, file):
    ''' this function is the master function for finding a if a file matches a type pattern.'''
    '''This function returns True if the argument looks like a file that would be copied to a LIB directory'''
    try:
        return is_category_file(env, cat, file.attributes.FilterAs)
    except AttributeError:
        patterns = env[cat]
        for i in patterns:
            if fnmatch.fnmatchcase(str(file), i):
                return True
        return False


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
