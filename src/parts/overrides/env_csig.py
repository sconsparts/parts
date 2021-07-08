'''
The Goal of this overide is to add the ability to get a CSig from an Environment object.

The CSig is only valid after a give part file and or SConscript is read in and make the assumption that
builders don't alter the state of the environment. This is generally a correct assumption as after the 
build files are read in the environment does not change. However there are always exceptions.

'''


import hashlib
from typing import Any
import types

import parts.glb as glb
import parts.core.util as util
import parts.api as api
import parts.platform_info
import parts.settings
import SCons
from SCons.Script.SConscript import SConsEnvironment


def str_value(key: str, value: Any, env: Any) -> str:
    '''
    Turns the object in to a str
    It checks the object for certain types to make sure
    they are handled correctly
    '''

    ret = ""
    if util.isString(value):
        ret = value
    elif isinstance(value, (int, float, complex)) or value is None:
        ret = str(value)
    elif isinstance(value, parts.settings.deprecated):
        # this case has a mapping to something else, so we ignore it
        ret = ""
    elif util.isNode(value):
        # if this is a not object we want to get the ID value for the sig
        ret = value.ID
    elif isinstance(value, SCons.Scanner.Base):
        # this is a scanner holder.. At the moment we skip this
        ret = ""
    elif isinstance(value, SCons.Action.ActionBase):
        # Get the action string for the ID
        # need to check if this is corrupted with function value with pointer values
        ret = value.genstring(["fake_target"], ["fake_source"], env)
    elif isinstance(value, (parts.platform_info.SystemPlatform)):
        # set of objects that we can just get the string value of
        ret = str(value)
    elif util.isList(value) or util.isTuple(value):
        # if this is a linear ordered collection
        ret = "["
        for v in value:
            ret += "{}, ".format(str_value(key, v, env))
        ret += "]"
    elif util.isSet(value):
        # this is a unordered collection
        ret = "set("
        for v in value:
            ret += "{}, ".format(str_value(key, v, env))
        ret += ")"
    elif util.isDictionary(value):
        # this is a dictionary or key:value collection
        ret = "{"
        for key, val in value.items():
            ret += "{}:{}".format(str_value(key, key, env), str_value(key, val, env))
        ret += "}"
    elif isinstance(value, type):
        # this is some type object
        ret = value.__module__ + value.__name__
    elif isinstance(value, types.FunctionType) or isinstance(value, types.MethodType):
        # this is function/callable type object
        ret = value.__module__ + value.__name__
    else:
        try:
            # this is an ugly test for this being a class
            ret = value.__class__
        except AttributeError:
            # well I don't know what it is at the moment
            api.output.warning_msgf(
                "Creating Environment CSig value.\n Skipping unknown type of:{type} key={key}", key=key, type=type(value))
    return ret


def default_handler(key: str, value: Any, env: Any) -> str:
    ret = "{0}:{1}".format(key, str_value(key, value, env))
    return ret


def get_csig(env, force=False) -> str:
    '''
    Get the signature of an environment object at a given point
    '''

    # check state... of reading in data files
    try:
        csig = env._env_csig
    except AttributeError:
        csig = None

    if not csig or force:
        # get value dictionary to handle special keys
        key_handler = env.get("ENV_KEY_HANDLER", {})
        md5 = hashlib.md5()
        try:
            #print(len(env.Dictionary()))
            tmp_dict = env.Dictionary()
            if '__builtins__' in tmp_dict:
                del tmp_dict['__builtins__']
            for key, value in tmp_dict.items():                
                handler = key_handler.get(key, default_handler)
                # handler functions returns some string we can add to the hash
                md5.update(handler(key, value, env).encode())
        except:
            #print("Oh no",len(env.Dictionary()))
            raise
        csig = md5.hexdigest()
        env._env_csig = csig

    return csig


SConsEnvironment.get_csig = get_csig
