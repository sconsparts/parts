
from typing import Dict
import os
import tempfile
import traceback
from collections import defaultdict

import _thread

import parts.api as api
import parts.common as common
import parts.core.util as util
import parts.errors as errors
import parts.glb as glb
import parts.part_ref as part_ref
import parts.policy as Policy
import parts.target_type as target_type
import parts.version as version
import SCons.Script
import SCons.Script.Main
import SCons.Subst
from SCons.Debug import logInstanceCreation
from SCons.Subst import CmdStringHolder


class env_guard:
    __slots__ = ('thread_id',)
    __depth__: Dict[int, int] = defaultdict(int)
    __cache__: Dict[int, int] = {}

    def __init__(self, thread_id=None):
        self.thread_id = thread_id or _thread.get_ident()

    def __enter__(self):
        depth = self.__depth__[self.thread_id]
        if depth == 0:
            # if depth is zero reset to None
            self.__cache__[self.thread_id] = True
        self.__depth__[self.thread_id] += 1
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__depth__[self.thread_id] -= 1
        depth = self.__depth__[self.thread_id]
        if depth == 0:
            # if depth is zero reset to None
            del self.__depth__[self.thread_id]
            del self.__cache__[self.thread_id]

    @classmethod
    def depth(cls, thread_id=None):
        return cls.__depth__[thread_id or _thread.get_ident()]

    @classmethod
    def cache(cls, val=None, thread_id=None):
        if val == False:
            cls.__cache__[thread_id or _thread.get_ident()] = val
        return cls.__cache__[thread_id or _thread.get_ident()]


class mapper:
    name = "Base"

    def __init__(self):
        self.stackframe = None  # errors.GetPartStackFrameInfo()

    def alias_missing(self, env):
        if env.get('MAPPER_BAD_ALIAS_AS_WARNING', True):

            api.output.warning_msg(self.name, "Alias", self.part_alias, "was not defined",
                                   "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>" %
                                   (env.PartName(), env.PartVersion(), env['TARGET_PLATFORM']),
                                   stackframe=self.stackframe
                                   )
        else:
            api.output.error_msg(
                self.name + " Alias", self.part_alias, "was not defined",
                "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>" %
                (env.PartName(), env.PartVersion(), env['TARGET_PLATFORM']),
                stackframe=self.stackframe,
                exit=False
            )
            # because the exception thrown will not get thrown the try catch in subst()
            env.Exit(1)

    def ref_to_part_failed(self, env, match, policy=Policy.ReportingPolicy.error):
        self.name_to_alias_failed(env, match, policy)

    def name_to_alias_failed(self, env, match, policy=Policy.ReportingPolicy.error):

        if match.hasAmbiguousMatch:
            reason = match.AmbiguousMatchStr()
        else:
            reason = match.NoMatchStr()
        api.output.policy_msg(
            policy,
            [self.name, 'mappers'],
            "Failed to map dependency for {0}\n  with Version: {1} config: {2} TARGET_PLATFORM: {3}\n {4}".format(
                env.PartName(), env.PartVersion(), env['CONFIG'], env['TARGET_PLATFORM'], reason),
            stackframe=self.stackframe,
            print_once=True,
            exit=False
        )
        if policy == Policy.ReportingPolicy.error:
            # because the exception thrown will not get thrown the try catch in subst()
            env.Exit(1)

    def _guarded_call(self, target, source, env, for_signature=False):
        raise NotImplementedError

    def _get_cache_hash(self, env):
        return (str(self), env.get_csig())  # get the sig key

    def __call__(self, target, source, env, for_signature=False):

        with env_guard():
            try:
                key = self._get_cache_hash(env)  # get the sig key
                ret = glb.subst_cache.get(key)  # do we have an item cached
                # do we have a dyn_export file
                # meaning we have some dynamic logic in a scanner
                dyn_export = env.get("DYN_EXPORT_FILE")
                # if we have an export test that it is built
                if dyn_export:
                    is_export_built = dyn_export.isBuilt or dyn_export.isVisited
                    env_guard.cache(is_export_built)

                # test if we can trust what is cached
                # we have to have loaded the part files
                if ret:
                    return ret
                else:
                    ret = self._guarded_call(target, source, env, for_signature)
                    if env_guard.cache() and glb.engine.BuildFilesLoaded:
                        glb.subst_cache[key] = ret

                return ret
            except SystemExit:
                raise
            except Exception as e:
                api.output.error_msg(
                    "Unexpected exception in {0} mapping happened\n mapper: \"{1!r}\"\n {2}\n{3}".format(
                        self.name, self, e, traceback.format_exc()),
                    stackframe=self.stackframe,
                    exit=False
                )
                # because the exception thrown will not get thrown the try catch in subst()
                env.Exit(1)


def _sub_lst(env, obj, thread_id):
    ret = []
    if util.isList(obj):
        for i in obj:
            tmp = _sub_lst(env, i, thread_id)
            if util.isList(tmp):
                common.extend_unique(ret, tmp)

    elif isinstance(obj, (SCons.Node.FS.Base, SCons.Subst.Literal, SCons.Subst.CmdStringHolder)):
        ret = [obj]
    else:
        if obj.startswith("$"):
            if obj.startswith("${") and obj.endswith('}'):
                tmpval = obj[2:-1]
            else:
                tmpval = obj[1:]
            try:
                replace_val = env[tmpval]
            except KeyError:
                tmp = env.subst(obj, conv=lambda x: x)
            else:
                return _sub_lst(env, replace_val, thread_id)
        else:
            tmp = env.subst(obj, conv=lambda x: x)

        if util.isList(tmp):
            with env_guard(thread_id):
                # todo add fix to not call _sub_list of item
                # is not a string with $ in it. This reduce stack depth stress
                for j in tmp:
                    r = _sub_lst(env, j, thread_id)
                    if r:
                        if util.isList(r[0]):
                            common.extend_unique(ret, r)
                        else:
                            common.append_unique(ret, r)
        else:
            if isinstance(tmp, SCons.Subst.CmdStringHolder):
                # this is needed as some bugs show up with str+CmdStringHolder concats
                # should not happen I think .. probally a bug at the moment in the subst engine
                tmp = [tmp]
            ret.append(tmp)

    return ret


def sub_lst(env, lst, thread_id, recurse=True):
    '''
    Utility function to help with returning list from env.subst() as this function
    doesn't like the returning of lists.
    '''

    with env_guard(thread_id):
        spacer = "." * env_guard.depth(thread_id)
        api.output.trace_msg(['sub_lst', 'mapper'], spacer, "sub_lst getting value for", lst)
        ret = []
        for v in lst[:]:
            tmp = _sub_lst(env, v, thread_id)
            if tmp and util.isList(tmp[0]):
                common.extend_unique(ret, tmp,)
            else:
                common.append_unique(ret, tmp)

        api.output.trace_msg(['sub_lst', 'mapper'], spacer, "sub_lst returning", ret)

        #if util.isList(ret[0]):
            #for sublst in ret:
                #if util.isList(sublst):
                    #sublst[:] = env.Flatten(sublst)

        return ret



def _concat(prefix, _list, suffix, env, f=lambda x: x, target=None, source=None):
    # this is generally the same as the SCons version
    # it differs in that we call a different subst list function
    # that will append unqiue items.
    if not _list:
        return _list
    elif util.isString(_list):
        _list = [_list]
    # fully expand the list

    # this does a append_unique of the items, so it should be
    # a unique list with everything in correct order
    tmp = sub_lst(env, _list, _thread.get_ident(), recurse=False)
    _list = env.Flatten(tmp)

    l = f(SCons.PathList.PathList(_list).subst_path(env, target, source))

    if l is not None:
        _list = l

    return _concat_ixes(prefix, _list, suffix, env)


_concat.name = "_concat"


def _concat_ixes(prefix, list, suffix, env):
    """
    Redo of the same logic in SCons... We just add it to the environment
    The functions adds a prefix and or suffix to the string value
    equals of the list
    """
    result = []

    # ensure that prefix and suffix are strings
    prefix = str(env.subst(prefix, SCons.Subst.SUBST_RAW))
    suffix = str(env.subst(suffix, SCons.Subst.SUBST_RAW))

    for x in list:
        if isinstance(x, SCons.Node.FS.File):
            result.append(x)
            continue
        x = str(x)
        if x:

            if prefix:
                if prefix[-1] == ' ':
                    result.append(prefix[:-1])
                elif x[:len(prefix)] != prefix:
                    x = prefix + x

            result.append(x)

            if suffix:
                if suffix[0] == ' ':
                    result.append(suffix[1:])
                elif x[-len(suffix):] != suffix:
                    result[-1] = result[-1] + suffix

    return result


_concat_ixes.name = "_concat_ixes"


class part_mapper(mapper):
    ''' This class maps the part property in the Part object. It then returns the value
    of the property for the requested part alias. It has to do a small hack to
    replace a the property in the actual Env else a SCons issue with subst and lists
    causes the subst to fail.
    '''
    name = 'PARTS'

    def __init__(self, alias, prop, ignore=False):
        if __debug__:
            logInstanceCreation(self, 'parts.mappers.part_mapper')
        mapper.__init__(self)
        self.part_alias = alias
        self.part_prop = prop
        self.ignore = ignore

    def __repr__(self):
        return "${{{0}('{1}','{2}',{3})}}".format(self.name, self.part_alias, self.part_prop, self.ignore)

    def _guarded_call(self, target, source, env, for_signature):
        thread_id = _thread.get_ident()
        spacer = "." * env_guard.depth(thread_id)

        api.output.trace_msg(['parts_mapper', 'mapper'], spacer, 'Expanding value "{0!r}"'.format(self))

        pobj = glb.engine._part_manager._from_alias(self.part_alias)
        if pobj is None:
            api.output.trace_msg(['parts_mapper', 'mapper'], spacer, 'Failed to find Part with Alias: {0}'.format(self.part_alias))
            self.alias_missing(env)
            return ''
        api.output.trace_msg(['parts_mapper', 'mapper'], spacer, 'Found Part with Alias: {0}'.format(self.part_alias))
        # try to map the part property
        ret = getattr(pobj, self.part_prop, None)
        if ret is None:
            # try again if that failed as lower case
            tmp = self.part_prop[0] + self.part_prop[1:].lower()
            ret = getattr(pobj, tmp, None)
        if ret is None:
            # error out if we still failed
            if self.ignore == False:
                api.output.warning_msg(self.name, "mapper: Property ",
                                       self.part_alias + '.' + self.part_prop, " was not defined",
                                       stackframe=self.stackframe
                                       )
            return ''
        api.output.trace_msg(['parts_mapper', 'mapper'], spacer, 'Property {0} = {1} '.format(self.part_prop, ret))
        penv = pobj.Env

        if util.isList(ret):
            return penv.subst_list(ret)
        return penv.subst(ret)


class part_id_mapper(mapper):
    ''' This class maps the part name and version range to the correct alias in
    the Default Environment to the actual value stored the in default Env PART_INFO map.
    It then returns the value of the property for the requested part alias.
    It has to do a small hack to replace a the property in the actual Env else a SCons
    issue with subst and lists causes the subst to fail.
    '''
    name = 'PARTID'

    def __init__(self, id, ver_range, part_prop, ignore=False):
        if __debug__:
            logInstanceCreation(self, 'parts.mappers.part_id_mapper')
        mapper.__init__(self)
        self.part_name = id
        self.ver_range = version.version_range(ver_range)
        self.part_prop = part_prop.lower()
        self.ignore = ignore

    def __repr__(self):
        return "${{{0}('{1}','{2}','{3}',{4})}}".format(self.name, self.part_name, self.ver_range, self.part_prop, self.ignore)

    def _guarded_call(self, target, source, env, for_signature):
        thread_id = _thread.get_ident()
        spacer = "." * env_guard.depth(thread_id)
        api.output.trace_msg(['partid_mapper', 'mapper'], spacer, 'Expanding value "{0!r}"'.format(self))

        # Find matching version pinfo
        t = target_type.target_type("name::" + self.part_name)
        t.Properties['version'] = self.ver_range
        t.Properties['platform_match'] = env['TARGET_PLATFORM']
        match = part_ref.PartRef(t, glb.engine._part_manager._from_env(env).Uses)
        if match.hasUniqueMatch:
            pobj = match.UniqueMatch
        else:
            api.output.trace_msg(['partid_mapper', 'mapper'], spacer,
                                 'Failed to find Part that matches name: {0}'.format(self.part_name))
            self.name_to_alias_failed(env, match, policy=Policy.REQPolicy.error)

        api.output.trace_msg(
            ['partid_mapper', 'mapper'],
            spacer, 'Found matching part! name: {0} version:{1} -> alias: {2}'.format(self.part_name, self.ver_range, pobj.Alias))

        ret = getattr(pobj, self.part_prop, None)
        if ret is None:
            if self.ignore == False:
                api.output.warning_msg(self.name, "mapper: Property ",
                                       pobj.Alias + '.' + self.part_prop, " was not defined",
                                       stackframe=self.stackframe
                                       )
            return ''
        api.output.trace_msg(['partid_mapper', 'mapper'], spacer, 'Property {0} = {1} '.format(self.part_prop, ret))
        penv = pobj.Env

        if util.isList(ret):
            return penv.subst_list(ret)
        return penv.subst(ret)


class part_id_export_mapper(mapper):
    ''' This class maps the part name and version range to the correct alias in
    the Default environment to the actual value stored the in default Env PART_INFO map.
    It then returns the value of the property for the requested part alias.
    It has to do a small hack to replace a the property in the actual Env else a SCons
    issue with subst and lists causes the subst to fail.
    '''
    name = 'PARTIDEXPORTS'

    def __init__(self, name, section, part_prop, policy=Policy.REQPolicy.warning, optional=False):
        if __debug__:
            logInstanceCreation(self, 'parts.mappers.part_id_export_mapper')
        mapper.__init__(self)
        self.part_name = name
        self.part_prop = part_prop
        self.policy = policy
        self.section = section
        self.optional = optional

    def __repr__(self):
        return f"${{{self.name}('{self.part_name}','{self.section}','{self.part_prop}',{self.policy},{self.optional})}}"

    def _guarded_call(self, target, source, env, for_signature):
        thread_id = _thread.get_ident()
        spacer = "." * env_guard.depth(thread_id)

        pobj_org = glb.engine._part_manager._from_env(env)
        api.output.trace_msg(['partexport_mapper', 'mapper'], spacer, 'Expanding value "{0!r}"'.format(self))

        # Find matching version pinfo
        match = part_ref.PartRef(target_type.target_type(self.part_name), pobj_org.Uses)
        if match.hasUniqueMatch:
            pobj = match.UniqueMatch
        elif match.hasStoredMatch:
            pobj = match.StoredUniqueMatch
        elif not match.hasUniqueMatch and self.optional:
            api.output.trace_msg(['partexport_mapper', 'mapper'], spacer,
                                 f'Failed to find Optional Part that matches name: {self.part_name}')
            #self.name_to_alias_failed(env, match, policy=Policy.REQPolicy.warning)
            return ''
        else:
            api.output.trace_msg(['partexport_mapper', 'mapper'], spacer,
                                 'Failed to find Part that matches name: {0}'.format(self.part_name))
            self.name_to_alias_failed(env, match, policy=self.policy)
            return ''

        api.output.trace_msg(['partexport_mapper', 'mapper'], spacer,
                             'Found matching part! name: {0} -> alias: {1}'.format(pobj.Name, pobj.Alias))

        psec = pobj.Section(self.section)
        penv = psec.Env
        # the question here is if the export table it up-to-date
        # normally this is probally the case. However if a build has a scanner that
        # add items to the export table dynamically this might not be true. Given no broken caching logic
        # all we want to do here it do an update check to unsure scanner went off that would have added
        # item to the export table. Given that this should be called again once the export table is updated
        # if
        ret = psec.Exports.get(self.part_prop, [])
        api.output.trace_msg(['partexport_mapper', 'mapper'], spacer, 'Property {0} = {1} '.format(self.part_prop, ret))

        # we need to test if this part has dynamic stuff that is unsafe to cache at this point in time
        dyn_export = penv.get("DYN_EXPORT_FILE")

        # if we have an export test that it is built
        if dyn_export:
            is_export_built = dyn_export.isBuilt or dyn_export.isVisited
        else:
            # else we just say it is for the cache test
            is_export_built = True

        env_guard.cache(is_export_built, thread_id)
        return ret


# deprecated .. better to use PARTSUBST()
class part_sub_mapper(mapper):
    ''' This class maps the part vars in the Default environment to the actual
    value stored the in default Env PART_INFO map. It then returns the value
    of the property for the requested part alias. This version doesn't have the
    small hack to fix the list subst in SCons. As such it a bit faster is is mostly
    used for delay substitution of more simple value such as $OUT_BIN which may contain
    values not fully filled in.
    '''
    name = 'PARTSUB'

    def __init__(self, part_alias, substr, section='build'):
        if __debug__:
            logInstanceCreation(self, 'parts.mappers.part_sub_mapper')
        mapper.__init__(self)
        self.part_alias = part_alias
        self.substr = substr
        self.section = section

    def __repr__(self):
        return "${{{0}('{1}','{2}','{3}')}}".format(self.name, self.part_alias, self.substr, self.section)

    def _guarded_call(self, target, source, env, for_signature):
        pobj = glb.engine._part_manager._from_alias(self.part_alias)
        if pobj is None:
            self.alias_missing(env)
            return None
        penv = pobj.Section(self.section).Env
        return penv.subst(self.substr, conv=lambda x: x)


class part_subst_mapper(mapper):
    ''' This class maps the part vars in the Default environment to the actual
    value stored the in default Env PART_INFO map. It then returns the value
    of the property for the requested part target. This version doesn't have the
    small hack to fix the list subst in SCons. As such it a bit faster is is mostly
    used for delay substitution of more simple value such as $OUT_BIN which may contain
    values not fully filled in.
    '''
    name = 'PARTSUBST'
    # probally need to remove section as the target shoudl handle this?

    def __init__(self, target_str, substr, section='build', policy=Policy.REQPolicy.warning):
        if __debug__:
            logInstanceCreation(self, 'parts.mappers.part_subst_mapper')
        mapper.__init__(self)
        self.target_str = target_str
        self.substr = substr
        self.section = section
        self.policy = policy

    def __repr__(self):
        return "${{{0}('{1}','{2}','{3}', {4})}}".format(self.name, self.target_str, self.substr, self.section, self.policy)

    def _guarded_call(self, target, source, env, for_signature):
        thread_id = _thread.get_ident()
        spacer = "." * env_guard.depth(thread_id)
        pobj_org = glb.engine._part_manager._from_env(env)
        ref = part_ref.PartRef(self.target_str, pobj_org.Uses)
        api.output.trace_msgf(['partsubst_mapper', 'mapper'], "{spacer}Mapping target: {0}", self.target_str, spacer=spacer)
        api.output.trace_msgf(['partsubst_mapper', 'mapper'], "{spacer}Has Match: {0}", ref.hasUniqueMatch, spacer=spacer)
        if not ref.hasUniqueMatch or not ref.hasMatch:
            self.ref_to_part_failed(env, ref, self.policy)
            api.output.trace_msgf(['partsubst_mapper', 'mapper'], "{spacer}Match failed: Returning None", spacer=spacer)
            return None

        pobj = ref.UniqueMatch
        penv = pobj.Section(self.section).Env
        ret = penv.subst(self.substr, conv=lambda x: x)
        api.output.trace_msgf(['partsubst_mapper', 'mapper'], "{spacer}Returning value of: {0}", ref.hasUniqueMatch, spacer=spacer)
        return ret


class part_name_mapper(mapper):
    ''' Allows for an easy fallback mapping between the part alias and name'''
    name = 'PARTNAME'

    def __init__(self, part_alias, env_var=None):
        if __debug__:
            logInstanceCreation(self, 'parts.mappers.part_name_mapper')
        mapper.__init__(self)
        self.part_alias = part_alias
        self.env_var = env_var

    def __repr__(self):
        return "${{{0}('{1}',{2})}}".format(self.name, self.part_alias,
                                            (self.env_var and "'{0}'".format(self.env_var) or None))

    def _guarded_call(self, target, source, env, for_signature):
        pobj = glb.engine._part_manager._from_alias(self.part_alias)
        try:
            ret = pobj.Name
        except AttributeError:
            self.alias_missing(env)
            return None
        if self.env_var:
            env[self.env_var] = ret
        if glb.engine.BuildFilesLoaded:
            glb.subst_cache[self._get_cache_hash(env)] = ret
        return ret


class part_shortname_mapper(mapper):
    '''
    Allows for an easy fallback mapping between the part short alias
    and short name
    '''
    name = 'PARTSHORTNAME'

    def __init__(self, part_alias):
        if __debug__:
            logInstanceCreation(self, 'parts.mappers.part_shortname_mapper')

        mapper.__init__(self)
        self.part_alias = part_alias

    def __repr__(self):
        return "${{{0}('{1}')}}".format(self.name, self.part_alias)

    def _guarded_call(self, target, source, env, for_signature):
        pobj = glb.engine._part_manager._from_alias(self.part_alias)

        if pobj is None:
            self.alias_missing(env)
            return None

        return pobj.ShortName


class define_if(mapper):
    '''if var is defined (ie positive bool value) return value '''
    name = 'define_if'

    def __init__(self, var, value):
        if __debug__:
            logInstanceCreation(self, 'parts.mappers.abspath_mapper')
        mapper.__init__(self)
        self.var = var  # var to subst
        self.value = value  # return if var is bool positive

    def __repr__(self):
        return f'${{{self.name}("{self.var},{self.value}")}}'

    def _guarded_call(self, target, source, env, for_signature):
        try:
            subvalue = env.subst(self.var)
        except Exception as e:
            subvalue = None
            api.output.verbose_msgf(['defineif_mapper', 'mapper', 'debug'], "Exception was caught during define_if mapper:\n {}", e)

        if subvalue:
            return self.value
        return ""


class abspath_mapper(mapper):
    ''' Allows for an easy expanding value as directory or file'''
    name = 'ABSPATH'

    def __init__(self, value):
        if __debug__:
            logInstanceCreation(self, 'parts.mappers.abspath_mapper')
        mapper.__init__(self)
        self.value = value

    def __repr__(self):
        return '${{{0}("{1}")}}'.format(self.name, self.value)

    def _guarded_call(self, target, source, env, for_signature):
        return env.Entry(env.subst(self.value)).abspath


class make_path(mapper):
    '''
    This class takes a list of values and constucts a PATH like string seperated via : or ;
    passes value in to a Dir() node to help normalize the "path"
    '''
    name = 'MAKEPATH'

    def __init__(self, varlist, pathsep=None, makeabs=True, unique=False):
        # sep == None means use system
        mapper.__init__(self)
        self.value = varlist
        self.pathsep = pathsep
        self.makeabs = makeabs
        self.unique = unique

    def __repr__(self):
        return '${{{0}("{1}","{2}","{3}")}}'.format(self.name, self.value, self.pathsep, self.makeabs)

    def _guarded_call(self, target, source, env, for_signature):
        values = env.Flatten(env.subst_list(self.value))
        if self.unique:
            # may need to allow more control of how it is made unique
            values = common.extend_unique([], values)
        ret = ""
        pathsep = self.pathsep if self.pathsep else os.pathsep

        for val in values:
            # scons barfs on it own CmdStringHolder
            if self.makeabs:
                ret += "{}{}".format(env.Dir(str(val)).abspath, pathsep)
            else:
                ret += "{}{}".format(env.Dir(str(val)), pathsep)
        if ret.endswith(pathsep):
            ret = ret[:-1]
        return ret


class join(mapper):
    '''
    This class takes a list of values a string joined via the token
    '''
    name = 'JOIN'

    def __init__(self, varlist, sep, unique=False):
        # sep == None means use system
        mapper.__init__(self)
        self.value = varlist
        self.sep = sep
        self.unique = unique

    def __repr__(self):
        return '${{{0}("{1}","{2}")}}'.format(self.name, self.value, self.sep)

    def _guarded_call(self, target, source, env, for_signature):
        values = env.Flatten(env.subst_list(self.value))
        if self.unique:
            # may need to allow more control of how it is made unique
            values = common.append_unique([], values)
        ret = self.sep.join([str(i) for i in values])
        return ret


class abspaths_mapper(mapper):
    '''
    Allows for an easy expanding value as a list directory's or files
    returns a list of values.
    '''
    name = 'ABSPATHS'

    def __init__(self, value):
        if __debug__:
            logInstanceCreation(self, 'parts.mappers.abspaths_mapper')
        mapper.__init__(self)
        self.value = value

    def __repr__(self):
        return '${{{0}("{1}")}}'.format(self.name, self.value)

    def _guarded_call(self, target, source, env, for_signature):
        vals = env.Flatten(env.subst_list(self.value))
        ret = []
        for val in vals:
            ret.append(env.Entry(str(val)).abspath)
        return ret


class normpath_mapper(mapper):
    ''' Allows for an easy expanding value as directory or files'''
    name = 'NORMPATH'

    def __init__(self, value):
        if __debug__:
            logInstanceCreation(self, 'parts.mappers.normpath_mapper')
        mapper.__init__(self)
        self.value = value

    def __repr__(self):
        return "${{{0}('{1}')}}".format(self.name, self.value)

    def _guarded_call(self, target, source, env, for_signature):
        if self.value[0] == '$':
            return env.Entry(env.subst(self.value)).path
        return env.Entry(env.subst("${" + self.value + "}")).path


class relpath_mapper(mapper):
    ''' allows one to define a relative path'''
    name = 'RELPATH'

    def __init__(self, _to, _from):
        if __debug__:
            logInstanceCreation(self, 'parts.mappers.relpath_mapper')
        mapper.__init__(self)
        self._to = _to
        self._from = _from

    def __repr__(self):
        return "${{{0}('{1}','{2}')}}".format(self.name, self._to, self._from)

    def _guarded_call(self, target, source, env, for_signature):
        if self._to[0] == '$':
            t = env.Entry(env.subst(self._to)).abspath
        t = env.Entry(env.subst("${" + self._to + "}")).abspath
        if self._from[0] == '$':
            f = env.Entry(env.subst(self._from)).abspath
        f = env.Entry(env.subst("${" + self._from + "}")).abspath
        return common.relpath(t, f) + os.sep


class runpath_mapper(mapper):

    name = 'GENRUNPATHS'

    def __init__(self, origin=r'$$$$$$$$ORIGIN'):
        self._origin = origin
        mapper.__init__(self)

    def __repr__(self):
        return "${{{0}('{1}')}}".format(self.name, self._origin)

    def _guarded_call(self, target, source, env, for_signature):

        # we have a system value given to us by the user
        # with will be added via RPATH before we get here
        # we want to leave that alone and just add the needed wrapper

        # we have generated rpaths based on install vs packaging locations
        # we will have AUTO_RPATH to control both values
        # we have AUTO_RUNPATH_INSTALL and PACKAGE_RUNPATH
        # AUTO_RUNPATH_INSTALL can be set at link time based on INSTALL_ROOT locations
        #   False no addition
        #   True/1 adds relative  $ORIGIN/../lib
        #   2 add paths as Absolute locations
        #   3 add both relative and absolute paths (rel then absolute)
        # PACKAGE_RUNPATH has to be done at packaging time, could require a relink
        #   however it is easier/faster to just use patch_elf to reset the value
        #   this does add to base tool requirements, but getting a relink would
        #   be very hard and error prone to get correct.
        # in this case we only worry about add the AUTO_RUNPATH_INSTALL
        auto_rpath = env.get('AUTO_RUNPATH_INSTALL', True)
        if env.get('AUTO_RPATH') and auto_rpath:
            do_rel = auto_rpath & 1
            do_abs = auto_rpath & 2
            # get the and values set by the user
            rlst = env.get('RPATH', [])
            rel_paths = []
            abs_paths = []
            # make a mapping between the bin and lib directories
            if env['HOST_OS'] == 'win32':
                quote = '"'
            else:
                quote = "'"

            # Apple requires absolute paths to be used
            # todo add the logic in for darwin
            if env['TARGET_OS'] != 'darwin':
                # add the dependent components
                # go over the depends if any
                # get the INSTALL_LIB locations for the component
                # Make a relative path for it and add it to the list
                # note most of the time these value are all the same
                # but this is not true all the time...
                # make a cache to speed up logic on "seen" items
                cache = set([])
                sec = glb.engine._part_manager.section_from_env(env)

                if sec:  # and sec.Depends:
                    # first add ourself first
                    rlst.append(
                        env.Literal(
                            '{0}{origin}/{1}{0}'.format(
                                quote,
                                env.Dir('$INSTALL_BIN').rel_path(
                                    env.Dir('$INSTALL_LIB')
                                ),
                                origin=self._origin
                            )
                        )
                    )

                    install_path = env.Dir('$INSTALL_BIN')
                    for comp in sec.Depends:
                        if not comp.hasUniqueMatch and comp.isOptional:
                            continue
                        libpath = comp.Section.Env.subst("$INSTALL_LIB")
                        if libpath not in cache:
                            cache.add(libpath)
                            if do_rel:
                                # compute relative value
                                rel_paths.append(
                                    env.Literal(
                                        '{0}{origin}/{1}{0}'.format(
                                            quote,
                                            install_path.rel_path(
                                                env.Dir(libpath)
                                            ),
                                            origin=self._origin
                                        )
                                    )
                                )

                            if do_abs:
                                abs_paths.append(env.Dir(libpath).abspath)

            return common.make_unique(rlst+rel_paths+abs_paths)


class pkgrunpath_mapper(mapper):

    name = 'GEN_PKG_RUNPATHS'

    def __init__(self, lib_paths, bin_path="$PACKAGE_BIN", origin=r'$$$$ORIGIN', use_origin=True):
        self._origin = origin
        self._lib_paths = lib_paths
        self._bin_path = bin_path
        self._use_origin = use_origin

        super(pkgrunpath_mapper, self).__init__()

    def __repr__(self):
        return "${{{0}('{1}','{2}','{3}','{4}')}}".format(self.name, self._lib_paths, self._bin_path, self._origin, self._use_origin)

    def _guarded_call(self, target, source, env, for_signature):

        # given the libpath value we make relative paths based on the PKG_BIN location via use of $ORIGIN
        # if we are to use_origin is false we use absolute path instead

        # do subst to get the list and finial values
        libpaths = env.Flatten(env.subst_list(self._lib_paths))
        binpath = env.Dir(self._bin_path)
        rlst = []
        # make a mapping between the bin and lib directories
        if env['HOST_OS'] == 'win32':
            quote = '"'
        else:
            quote = "'"

        if self._use_origin:
            for libpath in libpaths:
                libpath = env.Dir(str(libpath))
                rlst.append(
                    env.Literal(
                        '{0}{origin}/{1}{0}'.format(
                            quote,
                            binpath.rel_path(
                                libpath
                            ),
                            origin=self._origin
                        )
                    )
                )
        else:
            for libpath in libpaths:
                libpath = env.Dir(str(libpath))
                rlst.append(libpath.abspath)
        ret = common.make_unique(rlst)
        return ret


# these are some basic string items
class replace_mapper(mapper):
    ''' replace a character in subst value'''
    name = '_replace'

    def __init__(self, val, old, new, count=None):
        if __debug__:
            logInstanceCreation(self, 'parts.mappers.replace_mapper')
        mapper.__init__(self)
        self._val = val
        self._old = old
        self._new = new
        self._count = count

    def __repr__(self):
        return "${{{0}('{1}','{2}','{3}','{4}')}}".format(self.name, self._val, self._old, self._new, self._count)

    def _guarded_call(self, target, source, env, for_signature):
        tmp = env.subst(self._val)
        if self._count:
            tmp = tmp.replace(env.subst(self._old), env.subst(self._new), self._count)
        else:
            tmp = tmp.replace(env.subst(self._old), env.subst(self._new))
        return tmp


api.register.add_mapper(_concat)
# api.register.add_mapper(_concat_ixes)

api.register.add_mapper(define_if)
api.register.add_mapper(part_mapper)
api.register.add_mapper(part_id_mapper)
api.register.add_mapper(part_id_export_mapper)
api.register.add_mapper(part_sub_mapper)
api.register.add_mapper(part_subst_mapper)
api.register.add_mapper(part_name_mapper)
api.register.add_mapper(part_shortname_mapper)
api.register.add_mapper(make_path)
api.register.add_mapper(join)
api.register.add_mapper(abspath_mapper)
api.register.add_mapper(abspaths_mapper)
api.register.add_mapper(normpath_mapper)
api.register.add_mapper(relpath_mapper)
api.register.add_mapper(runpath_mapper)
api.register.add_mapper(pkgrunpath_mapper)
api.register.add_mapper(replace_mapper)

api.register.add_bool_variable('MAPPER_BAD_ALIAS_AS_WARNING', True, 'Controls if a missing alias is an error or a warning')
