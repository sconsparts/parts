from __future__ import absolute_import, division, print_function


from builtins import map

import SCons.Node.FS
from SCons.Debug import logInstanceCreation

import parts.api as api
import parts.common as common
import parts.core as core
import parts.glb as glb

# move to glb once we have new formats working
__known_concepts = {
    'utest': 'utest',
    'run_utest': 'utest',
    'build': 'build'
}


def is_concepts(val):
    return val in __known_concepts


def map_concept(val):
    return __known_concepts[val]


def get_concept(tlst):
    # see if the concept is defined

    # special 'all' case
    if tlst[0] == 'all' and len(tlst) == 1:
        return {'_section': 'build', '_recursive': True}, []
    # special case that is possibly ambiguous'
    if len(tlst) == 1 and "@" not in tlst[0]:
        return {'_section': 'build', '_recursive': False, '_ambiguous': True,
                '_name': tlst[0]}, []
    # special case of alias:: or name::
    if len(tlst) == 2 and tlst[0] in ['name', 'alias'] and not tlst[1]:
        return {'_section': 'build'}, ['']
    # some concept would have to be xxx:: else we assume it is a name
    elif is_concepts(tlst[0]) and len(tlst) > 1:
        # we have a concept defined
        section = map_concept(tlst[0])
        return {'_concept': tlst[0], '_section': section}, tlst[1:]

    # set default concept
    # value is hard coded at the moment
    return {'_section': 'build'}, tlst


def get_partrefdata(tok):

    if not tok:
        return {}, tok
    # <concpet>::
    elif len(tok) == 1 and tok[0] == '':
        return {}, tok
    # alias
    elif tok[0] == 'alias' and len(tok) == 1:
        return get_name(tok)
    # alias::??
    elif tok[0] == 'alias':
        return get_alias(tok[1:])
    # name or name@k,v...
    elif tok[0].startswith('name') and len(tok) == 1:
        return get_name(tok)
    # name::xxx
    elif tok[0] == 'name':
        return get_name(tok[1:])
    # xxx which we assume to be a name..
    elif tok[0] != '':
        return get_name(tok)
    # <concept>::::<group> or <concept>::::
    elif tok[0] == '':
        return {}, tok[1:]
    else:
        1 / 0  # not sure if we can get here...


def get_alias(tok):

    # <concept>::alias:: same as concept::
    if len(tok) == 1 and tok[0] == '':
        return {}, tok
    # <concept>::alias::::<group>
    elif tok[0] == '':
        return {}, tok[1:]
    # <concept>::alias::<alias>
    else:
        return {'_alias': tok[0]}, tok[1:]


def get_name(tok):

    # <concept>::name:: same as concept::
    if len(tok) == 1 and tok[0] == '':
        return {}, tok
    # <concept>::name::::<group>
    elif tok[0] == '':
        return {}, tok[1:]
    # name::@k,v
    elif tok[0].startswith('@'):
        tlst = tok[0].split("@")
        prop = get_properties(tlst[0])
        return {'_properties': prop}, tok[1:]
    # name::XXX@k,v
    else:
        tlst = tok[0].split("@")
        prop = get_properties(tlst[1:])
        return {'_name': tlst[0], '_properties': prop}, tok[1:]


def get_properties(tlst):
    properties = {}
    for p in tlst:
        try:
            # get key value
            k, v = p.split(":")
            # break up value into list
            vtmp = v.split(',')
            # remove exta junk at end if it exists
            if vtmp[-1] == '':
                vtmp = vtmp[:-1]
            # set if we have a list as a list
            if len(vtmp) > 1:
                properties[k] = vtmp
            else:
                # else this is a simple value ( non list)
                properties[k] = v
        except ValueError:
            api.output.error_msg('target value "%s" is bad, @property "%s" not splitable by ":"' % (target, p))
    return properties


def get_groups(tlst):
    # end of the line
    if not tlst:
        return {}, tlst
    # something like foo::::
    elif tlst[0] == '' and len(tlst) > 1:
        return {}, tlst[1:]
    # something like foo::
    elif tlst[0] == '' and len(tlst) == 1:
        return {}, tlst
    else:
        return {'_groups': tlst[0].split(',')}, tlst[1:]


def _parse_target(target):
    '''
    Parses the Target to help Parts figure out how to treat the Target

    The current logic is to handle cases such as:
    \verbatim
        alias::<part_alias>
        <part name>
        name::<part name>
        name::<part name>@key:value
        name::<part name>@key:value@key2:val2 ...
        name::<part name>@key:vala, valb, valc@key2:val2 ...
        <concept>::<some form from above>
        <concept>::<some form from above>::
    \endverbatim
    '''

    seperator = '::'
    # split in to major catagories
    t = target.split(seperator)
    ret = {}
    # does this have to many breaks... This is the max given values such a
    # build::name::foo::group::
    # however a case of build:::::::: is also to many as no name is provided
    if len(t) > 5:
        api.output.error_msg('target value "{0}" is bad, too many :: breaks'.format(target))
    # get the concept
    r, t = get_concept(t)
    ret.update(r)
    if not t:
        return ret
    # process reference data
    # returns a dict with values of all, alias, name, properties set
    r, t = get_partrefdata(t)
    ret.update(r)
    # process any groups
    r, t = get_groups(t)
    ret.update(r)
    # process the recurse
    if not t or t[0] != '':
        ret['_recursive'] = False
    else:
        ret['_recursive'] = True

    if len(t) > 1:
        api.output.error_msg('target value "{0}" is bad, too many :: breaks'.format(target))
    return ret


'''
target_type is a class that allow a quick parsing to allow one to figureout if
the target string part alias or Scons alias. it allow in the case of parts for
one to see what concept, part object, and section/concept we want to process
'''


class target_type(object):

    def __init__(self, target):
        if __debug__:
            logInstanceCreation(self)

        if isinstance(target, SCons.Node.FS.Base):
            target = SCons.Node.FS.get_default_fs().Dir('#').rel_path(target)
        else:
            target = str(target)
        self._properties = {}
        self._orginal_string = target
        self.__dict__.update(_parse_target(target))

    @property
    def Concept(self):
        try:
            return self._concept
        except AttributeError:
            return None

    @Concept.setter
    def Concept(self, value):
        if not value:
            try:
                del self._concept
            except AttributeError:
                pass
        else:
            self._concept = value

    @property
    def hasConcept(self):
        return hasattr(self, '_concept')

    @property
    def Section(self):
        try:
            return self._section
        except AttributeError:
            return None

    @Section.setter
    def Section(self, value):
        if not value:
            try:
                del self._section
            except AttributeError:
                pass
        else:
            self._section = value

    @property
    def hasSection(self):
        return hasattr(self, '_section')

    @property
    def Alias(self):
        try:
            return self._alias
        except AttributeError:
            return None

    @Alias.setter
    def Alias(self, value):
        if not value:
            try:
                del self._alias
            except AttributeError:
                pass
        else:
            self._alias = value

    @property
    def hasAlias(self):
        return hasattr(self, '_alias')

    @property
    def Name(self):
        try:
            return self._name
        except AttributeError:
            return None

    @Name.setter
    def Name(self, value):
        if not value:
            try:
                del self._name
            except AttributeError:
                pass
        else:
            self._name = value

    @property
    def hasName(self):
        return hasattr(self, '_name')

    @property
    def Properties(self):
        return self._properties

    @property
    def hasProperties(self):
        return bool(self._properties)

    @property
    def OrignialString(self):
        return self._orginal_string

    @property
    def RootAlias(self):
        if self.hasAlias:
            return self.Alias.split('.', 1)[0]
        return None

    @property
    def RootName(self):
        if self.hasName:
            return self.Name.split('.', 1)[0]
        return None

    @property
    def Groups(self):
        try:
            return self._groups
        except AttributeError:
            return tuple()

    @Groups.setter
    def Groups(self, value):
        if not value:
            try:
                del self._groups
            except AttributeError:
                pass
        else:
            self._groups = tuple(value)

    @property
    def hasGroups(self):
        return hasattr(self, '_groups')

    @property
    def isRecursive(self):
        try:
            return self._recursive
        except AttributeError:
            return False

    @property
    def isAmbiguous(self):
        try:
            return self._ambiguous
        except AttributeError:
            return False

    def setUnambiguous(self, value):
        try:
            del self._ambiguous
        except AttributeError:
            pass

    def __str__(self):
        '''
        Return a string form of target with any changed values.
        Use orginal_string value to get the orginal value used to Intially create this object
        '''
        s = ''
        if self.hasConcept:
            s += "{0}::".format(self.Concept)
        if self.hasAlias:
            s += "alias::{0}".format(self.Alias)
        elif self.hasName:
            s += "name::{0}".format(self.Name)
            for key, value in self.Properties.items():
                s += "@" + key + ":"
                s += ",".join(map(str, common.make_list(value)))
        elif not self.hasConcept:
            s += "{0}::".format(self.Section)

        if self.hasGroups:
            s += "::"
            s += ",".join(map(str, self.Groups))
        if self.isRecursive and not s.endswith("::"):
            s += "::"
        return s
