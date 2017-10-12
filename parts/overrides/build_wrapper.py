# this overide deals with allowing Parts to record what targets file a given Parts/component
# will create. It also adds support for the generic allow_duplicate value for all builders
# which allows a builder call that is called twice and that build the same target for different
# environments to ignore that one set was built, avoiding the warning or error from SCons about
# building duplicate files. This is nice for copying config files that are platform independent
# during a cross build.

# we used lists as a dictionary can't take a tuple as a key
# I could try to turn the key into a string however i was unsure of speed impact..
# deal with that latter

import SCons.Environment
import SCons.Builder
from .. import glb
from .. import errors

import os

key_list = []
value_list = []


# Orig_BuildWrapper=SCons.Environment.BuilderWrapper

Orig_call = SCons.Builder.BuilderBase.__call__

# class Parts_BuilderWrapper(Orig_BuildWrapper):

# def parts_call_(self, target=None, source=SCons.Environment._null, *args, **kw):


def parts_call_(self, env, target=None, source=None, chdir=SCons.Builder._null, **kw):
    # self.object should be the env value
    pobj = glb.engine._part_manager._from_env(env)

    # clean up source value to make it a list as the builder would expect it
    # this help me latter in dealing with the values myself
    # we don't make them real nodes as we don't know what the builder wants
    if SCons.Util.is_String(source) and source != '':
        source = [source]  # make it a list
    elif source == SCons.Environment._null:
        pass  # leave it alone
    elif SCons.Util.is_List(source):
        # flatten the list
        source = SCons.Util.flatten(source)

    dup = kw.get("allow_duplicates", False)
    found = False
    if dup:
        # Get info for help store info matches better
        if pobj is not None:
            name = pobj.Name
            srcpath = pobj.SourcePath
        else:
            name = None
            srcpath = None
        # make key

        if source == SCons.Environment._null:
            s = "_null"
        elif SCons.Util.is_List(source):
            s = [os.path.split(str(i))[1] for i in source]
        elif SCons.Util.is_String(source):
            s = source
        else:
            s = "_null"

        if target == []:
            key = (srcpath, s, self.get_name(env), name)
        else:
            key = (target, s, self.get_name(env), name)

        # test for match
        if key in key_list:
            tmp = value_list[key_list.index(key)]
            found = True
            kw['_found_duplication'] = True

    # if not found:
    try:
        tmp = self.Orig_call(env, target, source, chdir=chdir, **kw)
    except errors.AllowedDuplication:
        pass

    # take care of resolved target information.
    # for when we get a positive allow duplicate
    if dup:
        key_list.append(key)
        value_list.append(tmp)

    # don't add it to the Parts target list if this has no part or
    # if the actions here are part of a AutoConfigure set of calls
    # if pobj is not None and 'SConfSourceBuilder' not in self.object['BUILDERS']:
        # pobj._target_files.update(tmp)
    # else:
        # print tmp[0], 'missing'
        # pass
    return tmp

SCons.Builder.BuilderBase.__call__ = parts_call_
SCons.Builder.BuilderBase.Orig_call = Orig_call
#from SCons.Script.SConscript import SConsEnvironment

# override the builder wrapper to allow us to get the files defined in the scope of a part
# SCons.Environment.BuilderWrapper=Parts_BuilderWrapper
