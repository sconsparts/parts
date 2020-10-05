import types
import SCons

from . import is_a as util
import parts.settings
import parts.api as api

def asStr(obj) -> str:
    '''
    Turns the object in to a string that we can use express what this object is
    For example callable object comeback as a signature string via the SCons Action functions
    or a Scons node object returns as a Part ID string refering to the object.
    The main goal is to avoid CSIG value that would be built and to avoid pointer values
    the would show with the default str() built in so this string could be used to signitures
    values or hash values.
    '''

    ret = ""
    if util.isString(obj):
        ret = obj
    elif isinstance(obj, (int, float, complex)) or obj is None:
        ret = str(obj)
    elif isinstance(obj, parts.settings.deprecated):
        # this case has a mapping to something else, so we ignore it
        ret = ""
    elif util.isNode(obj):
        # if this is a node object we want to get the ID value for the sig
        # we want to make sure in this case we return the ID value
        # and the csig()
        ret = obj.ID
    elif isinstance(obj, SCons.Scanner.Base):
        # this is a scanner holder.. At the moment we skip this
        ret = ""
    elif isinstance(obj, SCons.Action.ActionBase):
        # Get the action string for the ID
        # need to check if this is corrupted with function value with pointer values
        #ret = value.genstring(["fake_target"], ["fake_source"], env)
        ret = obj.get_contents()
    elif isinstance(obj, (parts.platform_info.SystemPlatform)):
        # set of objects that we can just get the string value of
        ret = str(obj)
    elif util.isList(obj) or util.isTuple(obj):
        # if this is a linear ordered collection
        ret = "["
        for v in obj:
            ret += "{}, ".format(asStr(v))
        ret += "]"
    elif util.isSet(obj):
        # this is a unordered collection
        ret = "{"
        for v in obj:
            ret += "{}, ".format(asStr(v))
        ret += "}"
    elif util.isDictionary(obj):
        # this is a dictionary or key:value collection
        # may need to change to sort keys() first
        ret = "{"
        for key, val in obj.items():
            ret += "{}:{}".format(asStr(key), asStr(val))
        ret += "}"
    elif isinstance(obj, type):
        # this is some type object
        ret = SCons.Action._object_contents(obj)
        #ret = value.__module__ + value.__name__
    elif isinstance(obj, types.FunctionType) or isinstance(obj, types.MethodType):
        # this is function/callable type object
        ret = SCons.Action._object_contents(obj)
        #ret = value.__module__ + value.__name__
    else:
        try:
            # this is an ugly test for this being a class
            ret = obj.__class__
        except AttributeError:
            # well I don't know what it is at the moment
            api.output.warning_msgf("Unknown type of {type} in core.get_content()",type=type(obj))
            return None
    return ret
