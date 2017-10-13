
import common
import core.util as util
import api
import copy
from policy import REQPolicy, ReportingPolicy

from SCons.Debug import logInstanceCreation

_added_types = {}


class requirement(object):

    def __init__(self, key, internal=False, public=None, policy=None, mapper=None, listtype=None, weight=0):
        ''' Sets up the requirment object

        @param value The value to import
        @param internal True is the value should not be added to current Parts export table, False otherwise
        @param public True to value to global 'env' space, instead of just the namespace in the env object
        @param policy how to handle an item that could not be mapped, can be ignore, warn, or error
        @param mapper The mapper object to use for delayed mapping in classic formats, defaults to PARTIDEXPORTS
        @param listtype Tells if this type is a list type or not..
        '''
        if __debug__:
            logInstanceCreation(self)
        self._key = key
        self._internal = internal
        self._weight = weight
        if public is None:
            self._public = False
        else:
            self._public = public

        if policy is None:
            self._policy = REQPolicy.warning
        else:
            self._policy = policy

        if listtype is None:
            # do some simple check for seeing if this value should be treated as a list
            # ie XXXFLAGS,XXXDEFINES,XXXPATH ( add more as needed )
            if self.key.endswith('FLAGS') or\
                    self.key.endswith('DEFINES') or\
                    self.key.endswith('PATH'):
                self._listtype = True
                if public is None:
                    self._public = False
                if policy is None:
                    self._policy = REQPolicy.ignore
            else:
                self._listtype = False
        else:
            self._listtype = listtype

        if mapper is not None:
            self._mapper = mapper
        else:
            self._mapper = 'PARTIDEXPORTS'

    def value_mapper(self, name, section):
        return "${{{0}('{1}','{2}','{3}',{4})}}".format(self._mapper, name, section, self.key, self.policy)

    @property
    def is_list(self):
        return self._listtype

    @property
    def is_public(self):
        return self._public

    @property
    def is_internal(self):
        return self._internal

    @property
    def key(self):
        return self._key

    @property
    def policy(self):
        return self._policy

    def __call__(self, internal=None, public=None, policy=None):
        if internal is not None:
            self._internal = internal
        if public is not None:
            self._public = public
        if policy is not None:
            self._policy = policy
        return self

    # def __copy__(self):
    #    return requirement(self._key, self._internal, self._public, self._policy, self._mapper, self._listtype,self._weight)
    #
    # def __deepcopy__(self):
    #    return requirement(self._key, self._internal, self._public, self._policy, self._mapper, self._listtype,self._weight)

    def __or__(self, lhs):
        if util.isInt(lhs):
            return REQ([self])
        return REQ([self]) | lhs

    def __ror__(self, rhs):
        if util.isInt(rhs):
            return REQ([self])
        return REQ([self]) | rhs

    def __ior__(self, lhs):
        if util.isInt(lhs):
            return REQ([self])
        return REQ([self]) | lhs

    def __iter__(self):
        return [self].__iter__()

    def __str__(self):
        return "requirement(key={0} internal={1} public={2} policy={3}, weight={4})".format(
            self.key, self._internal, self._public, self._policy, self._weight)

    def __repr__(self):
        return "requirement(key={0} internal={1} public={2} policy={3}, weight={4})".format(
            self.key, self._internal, self._public, self._policy, self._weight)

    def __hash__(self):
        return hash(self.key)

    def __cmp__(self, rhs):
        return cmp(self.key, rhs.key)

    def Serialize(self):
        return {'key': self._key,
                'internal': self._internal,
                'public': self._public,
                'policy': self._policy,
                'mapper': self._mapper,
                'listtype': self._listtype,
                'weight': self._weight}


class requirement_set(object):

    def __init__(self, lst, weight=-1000):
        '''Construct a new requirement set object
         @param lst The set of value to add. The values can be a string to an existing defined requirement set, or a requriement object
         @param weight The weight to give every object in this set.

         It is important to note that the lst object is copied. We have to make sure all objects we might change state on, are not shared.
        '''
        if __debug__:
            logInstanceCreation(self)
        self._weight = weight
        self._values = []
        for i in lst:
            if isinstance(i, type('')):
                if i in _added_types:
                    items = _added_types[i][0]
                    for item in items._values:
                        tmp = copy.copy(item)
                        tmp._weight = weight
                        self._values.extend(tmp)
                    api.output.policy_msg(
                        _added_types[i][1], 'REQ', "REQ option {0} is deprecated and will be removed, please remove usage.".format(i))
                else:
                    api.output.warning_msg("{0} is not a registered REQ type. Skipping...".format(i))
            else:
                tmp = copy.copy(i)
                tmp._weight = weight
                self._values.append(tmp)

    def __call__(self, internal=None, public=None, policy=None):
        for v in self._values:
            v(internal, public, policy)
        return self

    def __copy__(self):
        return requirement_set(self._values, self._weight)

    def __deepcopy__(self, memo={}):
        return requirement_set(self._values, self._weight)

    def __or__(self, lhs):
        if util.isInt(lhs):
            return REQ(self._values, self._weight)
        return REQ(self._values, self._weight) | lhs

    def __ror__(self, rhs):
        if util.isInt(rhs):
            return REQ(self._values, self._weight)
        return REQ(self._values, self._weight) | rhs

    def __ior__(self, lhs):
        if util.isInt(lhs):
            return REQ(self._values, self._weight)
        return REQ(self._values, self._weight) | lhs

    def __iter__(self):
        return self._values.__iter__()

    def __str__(self):
        return "RequirementSet({0})".format(self._values)

    def __repr__(self):
        return "RequirementSet({0})".format(self._values)


def DefineRequirementSet(name, lst, policy=ReportingPolicy.ignore, weight=-1000):
    tmplst = []
    global _added_types
    for i in lst:
        if isinstance(i, requirement):
            tmplst.append(i)
        elif isinstance(i, type('')):
            try:
                tmplst.extend(_added_types[i][0]._values)
                api.output.policy_msg(_added_types[i][1], 'REQ',
                                      "REQ option {0} is deprecated and will be removed, please remove usage.".format(i))
            except KeyError:
                api.output.warning_msg(i, "not found when mapping requirments")
    _added_types[name] = (requirement_set(tmplst, weight), policy)


class requirement_internal(requirement):

    def __call__(self, internal=None, public=None, policy=None):
        if public:
            self._public = public
        if policy:
            self._policy = policy
        return self

# class requirement_set_internal(requirement_set):
#    def __call__(self,public=None, policy=None):
#
#        for i in self.__values:
#            i(internal,public,policy)
#
#        return self


class metaREQ(type):

    def __getattr__(self, name):
        internal = False
        if name.lower().endswith('_internal'):
            name = name[:-len('_internal')]
            internal = True
        if name in _added_types:
            if _added_types[name][1] != ReportingPolicy.ignore:
                api.output.warning_msg("REQ option {0} is deprecated and will be removed, please remove usage.".format(name))
            return copy.deepcopy(_added_types[name][0])(internal=internal)
        if internal:
            return requirement_internal(name, internal)
        return requirement(name, internal)


class REQ(object):
    __metaclass__ = metaREQ
    Policy = REQPolicy

    def __init__(self, lst=[], weight=None):
        if __debug__:
            logInstanceCreation(self, 'parts.requirement.REQ')
        self.__data = {}
        for i in lst:
            tmp = copy.copy(i)
            if weight:
                tmp._weight = weight
            self.__data[tmp.key] = tmp

    def __or__(self, rhs):
        tmp = set(self.__data.values())
        for i in rhs:
            try:
                # this allow stuff at the end of to win
                # and allow value in "sets" to have lesser weight
                # than explict values
                if self.__data[i.key]._weight <= i._weight:
                    tmp.remove(i)
                    tmp.add(i)
                else:
                    pass
            except KeyError:
                tmp.add(i)
        return REQ(tmp)

    def __len__(self):
        return len(self.__data)

    def issubset(self, other):
        for i in self:
            if i not in other:
                return False
        return True

    def intersection(self, other):
        ret = set()
        for i in self:
            if i in other:
                ret.add(i)
        return REQ(ret)

    def __contains__(self, lhs):
        try:
            return lhs.key in self.__data
        except AttributeError:
            for i in lhs:
                if i.key not in self.__data:
                    return False
                return True

    def __iter__(self):
        tmp = sorted(self.__data.values())
        return iter(tmp)

    def __str__(self):
        tmp = sorted(self.__data.values())
        return "REQ({0})".format(tmp)

    def __repr__(self):
        tmp = sorted(self.__data.values())
        return "REQ({0})".format(tmp)

    def Serialize(self):
        data = []
        t = sorted(self.__data.values())
        for i in t:
            data.append(i.Serialize())
        return data

    def Unserialize(self, data):

        for i in data:
            t = requirement(**i)
            self.__data[t.key] = t
        return self
