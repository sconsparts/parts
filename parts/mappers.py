import glb
import part_ref
import policy as Policy
import common
import version
import api.output
import errors
import target_type

import SCons.Script.Main
import SCons.Script
import SCons.Subst
import traceback
import thread
import os

from SCons.Debug import logInstanceCreation

from collections import defaultdict
class env_guard(object):
    __slots__ = ('thread_id',)
    __depth__ = defaultdict(int)
    def __init__(self, thread_id = None):
        self.thread_id = thread_id or thread.get_ident()
    def __enter__(self):
        self.__depth__[self.thread_id] += 1

    def __exit__(self, exc_type, exc_value, traceback):
        self.__depth__[self.thread_id] -= 1

    @classmethod
    def depth(cls, thread_id = None):
        return cls.__depth__[thread_id or thread.get_ident()]

    @classmethod
    def can_modify(cls, thread_id = None):
        return not cls.__depth__[thread_id or thread.get_ident()]

def replace_list_items(container, marker, replacement, wrap = lambda x: x):
    '''
    The function modifies container by removing all items equal to "marker",
    moving all items in "replacement" to the latest position of either "marker"
    or "replacement". Note that "marker" is one item while "replacement" is
    a sequence of items.
    See the unit-test for details.

    Returns the container.
    '''
    marker = (wrap(marker), wrap((marker,)))
    result = []
    marker_index, replacement_index, next_seq = -1, -1, 0
    for item in container:
        if item in marker:
            marker_index = len(result)
            continue
        elif next_seq < len(replacement):
            # For some reasons SCons may convert [x, y, z] in to [(x,), (y,), (z,)]
            # need to handle the case.
            if item in (replacement[next_seq], (replacement[next_seq],)):
                next_seq += 1
                result.append(item)
                if next_seq == len(replacement):
                    # remove the whole sequence from the result
                    del result[-(next_seq):]
                    replacement_index = len(result)
                    next_seq = 0
                continue
        result.append(item)
        next_seq = 0
    if marker_index < 0:
        # Nothing to remove. Return unmodified container.
        return container
    index = max(marker_index, replacement_index)
    result[index:index] = replacement
    container[:] = result
    return container

class mapper(object):
    def __init__(self):
        if __debug__: logInstanceCreation(self, 'parts.mappers.Base')
        self.stackframe = errors.GetPartStackFrameInfo()

    def alias_missing(self,env):
        if env.get('MAPPER_BAD_ALIAS_AS_WARNING',True):

            api.output.warning_msg(self.name,"Alias", self.part_alias,"was not defined",
                "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                stackframe = self.stackframe
                )
        else:
            api.output.error_msg(
                self.name+" Alias",self.part_alias,"was not defined",
                "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                stackframe = self.stackframe,
                exit = False
                )
            #because the exception thrown will not get thrown the try catch in subst()
            env.Exit(1)

    def name_to_alias_failed(self,env,match,policy = Policy.ReportingPolicy.error):

        if match.hasAmbiguousMatch:
            reason = match.AmbiguousMatchStr()
        else:
            reason = match.NoMatchStr()
        api.output.policy_msg(
            Policy.ReportingPolicy.error,
            [self.name,'mappers'],
            "Failed to map dependency for {0}\n  with Version: {1} config: {2} TARGET_PLATFORM: {3}\n {4}".format(env.PartName(),env.PartVersion(),env['CONFIG'],env['TARGET_PLATFORM'],reason),
            stackframe = self.stackframe,
            exit = False
            )
        #because the exception thrown will not get thrown the try catch in subst()
        env.Exit(1)

    @staticmethod
    def map_export_table(sec, prop, rvalue, value, spacer, recursed):
        try:
            export_table = sec.Exports[prop]
        except KeyError:
            if recursed:
                return []
            return value
        api.output.trace_msg(['partexport_mapper','mapper'],spacer,"Trying to replace value in export table")
        api.output.trace_msg(['partexport_mapper','mapper'],spacer,"Before Export value: {0}".format(export_table))

        try:
            result = replace_list_items(export_table, rvalue, value, wrap = lambda x: [x])
            def recurse_list(container):
                for item in container:
                    if common.is_list(item):
                        replace_list_items(item, rvalue, value)
                        recurse_list(item)
            recurse_list(result)
            if not result:
                del sec.Exports[prop]
            return result if recursed else value
        except (TypeError, KeyError):
            # This means export_table is a string or the value is a dictionary
            if common.is_string(value):
                sec.Exports[prop] = export_table.replace(rvalue,value)
            else:
                sec.Exports[prop] = value
            api.output.trace_msg(['partexport_mapper','mapper'],spacer,"After export value: {0}".format(export_table))
            return sec.Exports[prop]

    @staticmethod
    def map_global_var(env,prop,rvalue,value,spacer):
        api.output.trace_msg(['partexport_mapper','mapper'],spacer,"Trying to replace value in env[{0}]".format(prop))
        try:
            # see if we even have a key here to map
            # will throw if env does not have this key mapped
            api.output.trace_msg(['partexport_mapper','mapper'],spacer,"Before env value: {0}".format(env[prop]))
        except KeyError:
            return
        api.output.trace_msg(['partexport_mapper','mapper'],spacer,"Value to set: {0}".format(value))
        try:
            if common.is_list(env[prop]):
                replace_list_items(env[prop], rvalue, value)
            else:
                env[prop] = value
        except KeyError, e:
            api.output.trace_msg(['partexport_mapper','mapper'],spacer,"KeyError",e)
        except ValueError, e:
            api.output.trace_msg(['partexport_mapper','mapper'],spacer,"ValueError",e)
        api.output.trace_msg(['partexport_mapper','mapper'],spacer,"After env value: {0}".format(env[prop]))

    def _guarded_call(self, target, source, env, for_signature = False):
        raise NotImplemented()

    def __call__(self, target, source, env, for_signature = False):
        try:
            return self._guarded_call(target, source, env, for_signature)
        except SystemExit:
            raise
        except:
            api.output.error_msg(
                "Unexpected exception in {0} mapping happened\n mapper: \"{1!r}\"\n{2}".format(
                    self.name, self, traceback.format_exc()),
                stackframe = self.stackframe,
                exit = False
                )
            #because the exception thrown will not get thrown the try catch in subst()
            env.Exit(1)

def _sub_lst(env, obj, thread_id):
    ret = []
    if common.is_list(obj):
        for i in obj:
            tmp = _sub_lst(env,i,thread_id)
            if common.is_list(tmp):
                common.extend_unique(ret,tmp)
            else:
                common.append_unique(ret,tmp)
    elif isinstance(obj, (SCons.Node.FS.Base, SCons.Subst.Literal, SCons.Subst.CmdStringHolder)):
        ret = [obj]
    else:
        if obj.startswith("$"):
            #this value might be an list in the environment
            if obj.startswith("${") and obj.endswith('}'):
                tmpval = obj[2:-1]
            else:
                tmpval = obj[1:]
            try:
                replace_val = env[tmpval]
            except KeyError:
                tmp = env.subst(obj, conv = lambda x: x)
            else:
                return _sub_lst(env,replace_val,thread_id)
        else:
            tmp = env.subst(obj, conv = lambda x: x)

        if common.is_list(tmp):
            with env_guard(thread_id):
                for j in tmp:
                    r = _sub_lst(env,j,thread_id)
                    if r:
                        if common.is_list(r[0]):
                            common.extend_unique(ret,r)
                        else:
                            common.append_unique(ret,r)
        else:
            if isinstance(tmp,SCons.Subst.CmdStringHolder):
                # this is needed as some bugs show up with str+CmdStringHolder concats
                # should not happen I think .. probally a bug at the moment in the subst engine
                tmp = [tmp]
            ret.append(tmp)

    return ret

def sub_lst(env, lst, thread_id,recurse = True):
    ''' Utility function to help with returning list from env.subst() as this function
    doesn't like the returning of lists.'''
    spacer = "." * env_guard.depth(thread_id)
    def do_sub_lst():
        api.output.trace_msg(['sub_lst','mapper'],spacer,"sub_lst getting value for",lst)

        ret = []
        for v in lst[:]:
            tmp = _sub_lst(env,v,thread_id)
            if tmp and common.is_list(tmp[0]):
                common.extend_unique(ret,tmp,)
            else:
                common.append_unique(ret,tmp)

        api.output.trace_msg(['sub_lst','mapper'],spacer,"sub_lst returning",ret)

        return ret

    if recurse:
        with env_guard(thread_id):
            return do_sub_lst()
    return do_sub_lst()

def _concat(prefix, list, suffix, env, f = lambda x: x, target = None, source = None):
    if not list:
        return list
    elif common.is_string(list):
        list = [list]
    #fully expand the list

    # this does a append_unique of the items, so it should be
    # a unique list with everything in correct order
    tmp = sub_lst(env,list,thread.get_ident(),recurse = False)
    list = env.Flatten(tmp)

    l = f(SCons.PathList.PathList(list).subst_path(env, target, source))
    if l is not None:
        list = l

    return env['_concat_ixes'](prefix, list, suffix, env)
_concat.name = "_concat"

def _concat_ixes(prefix, list, suffix, env):
    """
    Redo of the same logic in SCons...
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
                    result[-1] = result[-1]+suffix

    return result

_concat_ixes.name = "_concat_ixes"

class part_mapper(mapper):
    ''' This class maps the part property in the Part object. It then returns the value
    of the property for the requested part alias. It has to do a small hack to
    replace a the property in the actual Env else a SCons issue with subst and lists
    causes the subst to fail.
    '''
    name = 'PARTS'
    def __init__(self,alias,prop,ignore = False):
        if __debug__: logInstanceCreation(self, 'parts.mappers.part_mapper')
        mapper.__init__(self)
        self.part_alias = alias
        self.part_prop = prop
        self.ignore = ignore

    def __repr__(self):
        return '${{{0}("{1}","{2}",{3})}}'.format(self.name,self.part_alias,self.part_prop,self.ignore)

    def _guarded_call(self, target, source, env, for_signature):
        thread_id = thread.get_ident()
        spacer = "."*env_guard.depth(thread_id)

        api.output.trace_msg(['parts_mapper','mapper'],spacer,'Expanding value "{0!r}"'.format(self))

        pobj = glb.engine._part_manager._from_alias(self.part_alias)
        if pobj is None:
            api.output.trace_msg(['parts_mapper','mapper'],spacer,'Failed to find Part with Alias: {0}'.format(self.part_alias))
            self.alias_missing(env)
            return ''
        api.output.trace_msg(['parts_mapper','mapper'],spacer,'Found Part with Alias: {0}'.format(self.part_alias))
        ret = getattr(pobj,self.part_prop,None)
        if ret is None:
            tmp = self.part_prop[0]+self.part_prop[1:].lower()
            ret = getattr(pobj,tmp,None)
        if ret is None:
            if self.ignore == False:
                api.output.warning_msg(self.name,"mapper: Property ",
                    self.part_alias+'.'+self.part_prop," was not defined",
                    stackframe = self.stackframe
                    )
            return ''
        api.output.trace_msg(['parts_mapper','mapper'],spacer,'Property {0} = {1} '.format(self.part_prop,ret))
        penv = pobj.Env
        if common.is_list(ret):
            if len(ret)>1:
                ret = sub_lst(penv,ret,thread_id)

            setattr(pobj,self.part_prop,ret)
            if env_guard.can_modify(thread_id):
                api.output.trace_msg(['parts_mapper','mapper'],spacer,"Trying to replace value in env[{0}]".format(self.part_prop))
                api.output.trace_msg(['parts_mapper','mapper'],spacer,"Before env value: {0}".format(env[self.part_prop]))
                api.output.trace_msg(['parts_mapper','mapper'],spacer,"Value to set: {0}".format(ret))
                if common.is_list(env[self.part_prop]):
                    if ret:
                        rvalue = "${{{name}('{part_alias}','{part_prop}')}}".format(**self.__dict__)
                        replace_list_items(env[self.part_prop], rvalue, ret)
                else:
                    env[self.part_prop] = [ret]
                api.output.trace_msg(['parts_mapper','mapper'],spacer,"After env value: {0}".format(env[self.part_prop]))
                if not ret:
                    api.output.trace_msg(['parts_mapper','mapper'],spacer,"Returning (1) value of {0}".format("''"))
                    return ""
                else:
                    api.output.trace_msg(['parts_mapper','mapper'],spacer,"Returning (2) value of {0}".format(ret[0]))
                    return ret[0]
            else:
                tmp = ret
                api.output.trace_msg(['parts_mapper','mapper'],spacer,"Returning (3) value of '{0}'".format(ret))
                return tmp
        else:
            tmp = penv.subst(ret, conv = lambda x: x)
            api.output.trace_msg(['parts_mapper','mapper'],spacer,"Returning (4) value of {0}".format(tmp))
            return tmp

        return ret

class part_id_mapper(mapper):
    ''' This class maps the part name and version range to the correct alias in
    the Default enviroment to the actual value stored the in default Env PART_INFO map.
    It then returns the value of the property for the requested part alias.
    It has to do a small hack to replace a the property in the actual Env else a SCons
    issue with subst and lists causes the subst to fail.
    '''
    name = 'PARTID'
    def __init__(self,id,ver_range,part_prop,ignore = False):
        if __debug__: logInstanceCreation(self, 'parts.mappers.part_id_mapper')
        mapper.__init__(self)
        self.part_name = id
        self.ver_range = version.version_range(ver_range)
        self.part_prop = part_prop.lower()
        self.ignore = ignore

    def __repr__(self):
        return '${{{0}("{1}","{2}","{3}",{4})}}'.format(self.name,self.part_name,self.ver_range,self.part_prop,self.ignore)

    def _guarded_call(self, target, source, env, for_signature):
        thread_id = thread.get_ident()
        spacer = "."*env_guard.depth(thread_id)
        api.output.trace_msg(['partid_mapper','mapper'],spacer,'Expanding value "{0!r}"'.format(self))

        #Find matching verion pinfo
        t = target_type.target_type("name::"+self.part_name)
        t.Properties['version'] = self.ver_range
        t.Properties['platform_match'] = env['TARGET_PLATFORM']
        match = part_ref.part_ref(t)
        if match.hasUniqueMatch:
            pobj = match.UniqueMatch
        else:
            api.output.trace_msg(['partid_mapper','mapper'],spacer,'Failed to find Part that matches name: {0}'.format(self.part_name))
            self.name_to_alias_failed(env,match,policy = Policy.REQPolicy.error)

        api.output.trace_msg(['partid_mapper','mapper'],spacer,'Found matching part! name: {0} version:{1} -> alias: {2}'.format(self.part_name,self.ver_range,pobj.Alias))

        ret = getattr(pobj,self.part_prop,None)
        if ret is None:
            if self.ignore == False:
                api.output.warning_msg(self.name,"mapper: Property ",
                    pobj.Alias+'.'+self.part_prop," was not defined",
                    stackframe = self.stackframe
                    )
            return ''
        api.output.trace_msg(['partid_mapper','mapper'],spacer,'Property {0} = {1} '.format(self.part_prop,ret))

        penv = pobj.Env

        if common.is_list(ret):
            if ret:
                ret = sub_lst(penv, ret, thread_id)
            if env_guard.can_modify(thread_id):
                api.output.trace_msg(['partid_mapper','mapper'],spacer,"Trying to replace value in env[{0}]".format(self.part_prop))
                api.output.trace_msg(['partid_mapper','mapper'],spacer,"Before env value: {0}".format(env[self.part_prop]))
                api.output.trace_msg(['partid_mapper','mapper'],spacer,"Value to set: {0}".format(ret))

                if common.is_list(env[self.part_prop]):
                    if ret:
                        if self.ignore:
                            rvalue = "${{{name}('{part_name}','{ver_range}','{part_prop}',{ignore})}}"
                        else:
                            rvalue = "${{{name}('{part_name}','{ver_range}','{part_prop}')}}}"
                        replace_list_items(env[self.part_prop], rvalue.format(**self.__dict__), ret)
                else:
                    env[self.part_prop] = [ret]
                api.output.trace_msg(['partid_mapper','mapper'],spacer,"After env value: {0}".format(env[self.part_prop]))
                if not ret:
                    api.output.trace_msg(['partid_mapper','mapper'],spacer,"Returning (1) value of {0}".format("''"))
                    return ""
                else:
                    api.output.trace_msg(['partid_mapper','mapper'],spacer,"Returning (2) value of {0}".format(ret[0]))
                    return ret[0]
            else:
                tmp = ret
                api.output.trace_msg(['partid_mapper','mapper'],spacer,"Returning (3) value of '{0}'".format(ret))
                return tmp
        else:
            tmp = penv.subst(ret, conv = lambda x: x)
            api.output.trace_msg(['partid_mapper','mapper'],spacer,"Returning (4) value of {0}".format(tmp))
            return tmp

        return ret

class part_id_export_mapper(mapper):
    ''' This class maps the part name and version range to the correct alias in
    the Default enviroment to the actual value stored the in default Env PART_INFO map.
    It then returns the value of the property for the requested part alias.
    It has to do a small hack to replace a the property in the actual Env else a SCons
    issue with subst and lists causes the subst to fail.
    '''
    name = 'PARTIDEXPORTS'
    def __init__(self,name,section,part_prop,policy = Policy.REQPolicy.warning):
        if __debug__: logInstanceCreation(self, 'parts.mappers.part_id_export_mapper')
        mapper.__init__(self)
        self.part_name = name
        #self.ver_range = version.version_range(ver_range)
        self.part_prop = part_prop
        self.policy = policy
        self.section = section

    def __repr__(self):
        return '${{{0}("{1}","{2}","{3}",{4})}}'.format(self.name,self.part_name,self.section,self.part_prop,self.policy)

    def _guarded_call(self, target, source, env, for_signature):
        thread_id = thread.get_ident()
        spacer = "."*env_guard.depth(thread_id)

        pobj_org = glb.engine._part_manager._from_env(env)
        sec = pobj_org.DefiningSection
        api.output.trace_msg(['partexport_mapper','mapper'],spacer,'Expanding value "{0!r}"'.format(self))

        #Find matching version pinfo
        match = part_ref.part_ref(target_type.target_type(self.part_name),pobj_org.Uses)
        if match.hasUniqueMatch:
            pobj = match.UniqueMatch
        elif match.hasStoredMatch:
            pobj = match.StoredUniqueMatch
        else:
            api.output.trace_msg(['partexport_mapper','mapper'],spacer,'Failed to find Part that matches name: {0}'.format(self.part_name))
            self.name_to_alias_failed(env,match,policy = self.policy)

        api.output.trace_msg(['partexport_mapper','mapper'],spacer,'Found matching part! name: {0} -> alias: {1}'.format(pobj.Name,pobj.Alias))

        psec = pobj.Section(self.section)
        penv = psec.Env

        ret = psec.Exports.get(self.part_prop,[])
        api.output.trace_msg(['partexport_mapper','mapper'],spacer,'Property {0} = {1} '.format(self.part_prop,ret))

        #if we get back a list, we want to fill in the data in the list
        if common.is_list(ret):
            ret = sub_lst(penv,ret,thread_id)

        # update the export table
        str_val = "${{{0}('{1}','{2}','{3}',{4})}}".format(self.name,self.part_name,self.section,self.part_prop,self.policy)

        # update export table
        ret = self.map_export_table(sec, self.part_prop, str_val, ret, spacer,
                not env_guard.can_modify(thread_id))

        # only update the environment of the item that started the subst call.
        if env_guard.can_modify(thread_id):
            # we have data.. but we need to tweak the data to not piss SCons off
            # scons does not expect a list back or a list of lists.. only a string
            # Here we need to flatten the list
            ret = filter(None,env.Flatten(ret))
            self.map_global_var(env,self.part_prop,str_val,ret,spacer)
            if ret == []:
                api.output.trace_msg(['partexport_mapper','mapper'],spacer,"Returning (1) value of {0}".format("''"))
                return ''
            else:
                api.output.trace_msg(['partexport_mapper','mapper'],spacer,"Returning (2) value of {0}".format(ret[0]))
                return ret[0]
        else:
            #this case we have a list of stuff. we pickle it to get it throught the SCons subst engine
            pret = ret
            api.output.trace_msg(['partexport_mapper','mapper'],spacer,"Returning (3) value of '{0}'".format(ret))
            return pret

        # we don't have list so we just return the whole value
        tmp = penv.subst(ret, conv = lambda x: x)
        api.output.trace_msg(['partexport_mapper','mapper'],spacer,"Returning (4) value of {0}".format(tmp))
        return tmp

class part_subst_mapper(mapper):
    ''' This class maps the part vars in the Default enviroment to the actual
    value stored the in default Env PART_INFO map. It then returns the value
    of the property for the requested part alias. This version doesn't have the
    small hack to fix the list subst in SCons. As such it a bit faster is is mostly
    used for delay substiution of more simple value such as $OUT_BIN which may contain
    values not fully filled in.
    '''
    name = 'PARTSUB'
    def __init__(self,part_alias,substr,section = 'build'):
        if __debug__: logInstanceCreation(self, 'parts.mappers.part_subst_mapper')
        mapper.__init__(self)
        self.part_alias = part_alias
        self.substr = substr
        self.section = section

    def __repr__(self):
        return '${{{0}("{1}","{2}","{3}")}}'.format(self.name, self.part_alias, self.substr, self.section)

    def _guarded_call(self, target, source, env, for_signature):
        def_env = SCons.Script.DefaultEnvironment()

        pobj = glb.engine._part_manager._from_alias(self.part_alias)
        if pobj is None:
            self.alias_missing(env)
            return None
        penv = pobj.Section(self.section).Env
        return penv.subst(self.substr, conv = lambda x: x)

        return ret

class part_name_mapper(mapper):
    ''' Allows for an easy fallback mapping between the part alias and name'''
    name = 'PARTNAME'
    def __init__(self,part_alias,env_var = None):
        if __debug__: logInstanceCreation(self, 'parts.mappers.part_name_mapper')
        mapper.__init__(self)
        self.part_alias = part_alias
        self.env_var = env_var

    def __repr__(self):
        return '${{{0}("{1}",{2})}}'.format(self.name, self.part_alias,
                (self.env_var and '"{0}"'.format(self.env_var) or None))

    def _guarded_call(self, target, source, env, for_signature):
        pobj = glb.engine._part_manager._from_alias(self.part_alias)
        try:
            ret = pobj.Name
        except AttributeError:
            self.alias_missing(env)
            return None
        if self.env_var:
            env[self.env_var] = ret
        return ret

class part_shortname_mapper(mapper):
    '''
    Allows for an easy fallback mapping between the part short alias
    and short name
    '''
    name = 'PARTSHORTNAME'
    def __init__(self,part_alias):
        if __debug__: logInstanceCreation(self, 'parts.mappers.part_shortname_mapper')

        mapper.__init__(self)
        self.part_alias = part_alias

    def __repr__(self):
        return '${{{0}("{1}")}}'.format(self.name, self.part_alias)

    def _guarded_call(self, target, source, env, for_signature):
        pobj = glb.engine._part_manager._from_alias(self.part_alias)

        if pobj is None:
            self.alias_missing(env)
            return None

        return pobj.ShortName

class abspath_mapper(mapper):
    ''' Allows for an easy expanding value as directory or files'''
    name = 'ABSPATH'
    def __init__(self,value):
        if __debug__: logInstanceCreation(self, 'parts.mappers.abspath_mapper')
        mapper.__init__(self)
        self.value = value

    def __repr__(self):
        return '${{{0}("{1}")}}'.format(self.name, self.value)

    def _guarded_call(self, target, source, env, for_signature):
        if self.value[0] == '$':
            return env.Entry(env.subst(self.value)).abspath
        return env.Entry(env.subst("${"+self.value+"}")).abspath

class normpath_mapper(mapper):
    ''' Allows for an easy expanding value as directory or files'''
    name = 'NORMPATH'
    def __init__(self,value):
        if __debug__: logInstanceCreation(self, 'parts.mappers.normpath_mapper')
        mapper.__init__(self)
        self.value = value

    def __repr__(self):
        return '${{{0}("{1}")}}'.format(self.name, self.value)

    def _guarded_call(self, target, source, env, for_signature):
        if self.value[0] == '$':
            return env.Entry(env.subst(self.value)).path
        return env.Entry(env.subst("${"+self.value+"}")).path

class relpath_mapper(mapper):
    ''' allows one to define a relative path'''
    name = 'RELPATH'
    def __init__(self,_to,_from):
        if __debug__: logInstanceCreation(self, 'parts.mappers.relpath_mapper')
        mapper.__init__(self)
        self._to = _to
        self._from = _from

    def __repr__(self):
        return '${{{0}("{1}","{2}")}}'.format(self.name, self._to, self._from)

    def _guarded_call(self, target, source, env, for_signature):
        if self._to[0] == '$':
            t = env.Entry(env.subst(self._to)).abspath
        t = env.Entry(env.subst("${"+self._to+"}")).abspath
        if self._from[0] == '$':
            f = env.Entry(env.subst(self._from)).abspath
        f = env.Entry(env.subst("${"+self._from+"}")).abspath
        return common.relpath(t,f)+os.sep


import tempfile
from SCons.Subst import CmdStringHolder
class TempFileMunge(mapper):

    """A callable class.  You can set an Environment variable to this,
    then call it with a string argument, then it will perform temporary
    file substitution on it.  This is used to circumvent the long command
    line limitation.

    By default, the name of the temporary file used begins with a
    prefix of '@'.  This may be configred for other tool chains by
    setting '$TEMPFILEPREFIX'.

    env["TEMPFILEPREFIX"] = '-@'        # diab compiler
    env["TEMPFILEPREFIX"] = '-via'      # arm tool chain

    This is the Parts overide of the SCons version of this class
    to address a some complex issues with path handling when on
    windows and using GNU like tool chains

    todo.. push back into SCons

    """
    class result(str, CmdStringHolder):
        literal = False
        def __new__(cls, prefix, native_tmp, id):
            return super(TempFileMunge.result, cls).__new__(cls, prefix + native_tmp)
        def __init__(self, prefix, native_tmp, id):
            self.id = ("Using tempfile "+native_tmp+" for command line:\n" + id)
            self.native_tmp = native_tmp

        def __del__(self):
            try:
                os.unlink(self.native_tmp)
            except AttributeError:
                pass

        @property
        def data(self):
            return str(self)

    name = 'TEMPFILE'
    def __init__(self, cmd, force_posix_paths = False):
        if __debug__: logInstanceCreation(self, 'parts.mappers.TempFileMunge')
        self.cmd = cmd
        self.force_posix_paths = force_posix_paths

    def __call__(self, target, source, env, for_signature):
        if for_signature:
            # If we're being called for signature calculation, it's
            # because we're being called by the string expansion in
            # Subst.py, which has the logic to strip any $( $) that
            # may be in the command line we squirreled away.  So we
            # just return the raw command line and let the upper
            # string substitution layers do their thing.
            return self.cmd

        # Now we're actually being called because someone is actually
        # going to try to execute the command, so we have to do our
        # own expansion.
        cmd = env.subst_list(self.cmd, SCons.Subst.SUBST_CMD, target, source)[0]
        try:
            maxline = int(env.subst('$MAXLINELENGTH'))
        except ValueError:
            maxline = 2048

        length = 0
        for c in cmd:
            length += len(c)
        if length <= maxline:
            return self.cmd

        # We do a normpath because mktemp() has what appears to be
        # a bug in Windows that will use a forward slash as a path
        # delimiter.  Windows's link mistakes that for a command line
        # switch and barfs.
        #
        # We use the .lnk suffix for the benefit of the Phar Lap
        # linkloc linker, which likes to append an .lnk suffix if
        # none is given.
        (fd, tmp) = tempfile.mkstemp('.lnk', text = True)
        native_tmp = SCons.Util.get_native_path(os.path.normpath(tmp))

        if env['SHELL'] and env['SHELL'] == 'sh':
            # The sh shell will try to escape the backslashes in the
            # path, so unescape them.
            native_tmp = native_tmp.replace('\\', '/')

        prefix = env.subst('$TEMPFILEPREFIX')
        if not prefix:
            prefix = '@'

        args = list(map(SCons.Subst.quote_spaces, cmd[1:]))
        data = " ".join(args)
        #This is a little bit of a hack as it could mess up switches using '\'
        # however this is unlikely as windows uses / or - for switchs and posix uses - or --
        if self.force_posix_paths:
            data = data.replace('\\', '/')
        os.write(fd, data + "\n")
        os.close(fd)
        command_id = ' '.join((SCons.Subst.quote_spaces(cmd[0]), data))
        command_args = self.result(prefix, native_tmp, command_id)
        # XXX Using the SCons.Action.print_actions value directly
        # like this is bogus, but expedient.  This class should
        # really be rewritten as an Action that defines the
        # __call__() and strfunction() methods and lets the
        # normal action-execution logic handle whether or not to
        # print/execute the action.  The problem, though, is all
        # of that is decided before we execute this method as
        # part of expanding the $TEMPFILE construction variable.
        # Consequently, refactoring this will have to wait until
        # we get more flexible with allowing Actions to exist
        # independently and get strung together arbitrarily like
        # Ant tasks.  In the meantime, it's going to be more
        # user-friendly to not let obsession with architectural
        # purity get in the way of just being helpful, so we'll
        # reach into SCons.Action directly.
        if SCons.Action.print_actions:
            print command_args.id
        return [ cmd[0], command_args ]


api.register.add_mapper(_concat)
api.register.add_mapper(_concat_ixes)

api.register.add_mapper(part_mapper)
api.register.add_mapper(part_id_mapper)
api.register.add_mapper(part_id_export_mapper)
api.register.add_mapper(part_subst_mapper)
api.register.add_mapper(part_name_mapper)
api.register.add_mapper(part_shortname_mapper)
api.register.add_mapper(abspath_mapper)
api.register.add_mapper(normpath_mapper)
api.register.add_mapper(relpath_mapper)

api.register.add_mapper(TempFileMunge)

api.register.add_bool_variable('MAPPER_BAD_ALIAS_AS_WARNING',True,'Controls if a missing alias is an error or a warning')
