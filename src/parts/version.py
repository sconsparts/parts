'''
version and version_range implementation to make life easier when dealing with
version strings.
'''
from __future__ import absolute_import, division, print_function

import re
from builtins import map, range

import parts.api as api
from SCons.Debug import logInstanceCreation
from SCons.Script.SConscript import SConsEnvironment

__all__ = [
    'version',
    'version_range',
]


class VersionPart(object):
    '''
    Gives a part of a version number a way to store the string value and a
    weight associated with that string.
    '''
    __slots__ = ["ver", "alwaysMatch", "weight"]

    _matchSet = ['*', 'x', 'X']

    def __init__(self, strVer, weight=None):
        '''
        Initialize the part and do a little bit of parsing to decern if this is
        a match part.
        '''
        if __debug__:
            logInstanceCreation(self)
        self.ver = strVer
        self.alwaysMatch = strVer in self._matchSet
        self.weight = weight

    def compare(self, rhs, comp):
        '''
        Here is where the actual comparison is performed.  If either part has a
        weight, that weight is used in place of the version.  In any other case,
        version is used directly.  'comp' is used as the comparison operator.
        '''
        num1 = self.ver
        if self.weight is not None:
            num1 = self.weight

        try:
            num2 = rhs.ver
            if rhs.weight is not None:
                num2 = rhs.weight
        except AttributeError:
            num2 = rhs

        return comp(num1, num2)

    def __eq__(self, rhs):
        '''
        Check for equivalence.
        '''
        return self.compare(rhs, lambda x, y: x == y)

    def __ne__(self, rhs):
        '''
        Check for not-equal.
        '''
        return self.compare(rhs, lambda x, y: x != y)

    def __lt__(self, rhs):
        '''
        Check for less than.
        '''
        return self.compare(rhs, lambda x, y: x < y)

    def __le__(self, rhs):
        '''
        Check for less or equal.
        '''
        return self.compare(rhs, lambda x, y: x <= y)

    def __gt__(self, rhs):
        '''
        Check for greater than.
        '''
        return self.compare(rhs, lambda x, y: x > y)

    def __ge__(self, rhs):
        '''
        Check for greater or equal.
        '''
        return self.compare(rhs, lambda x, y: x >= y)

    def __str__(self):
        '''
        Print the string form which just returns the passed in version string.
        '''
        return "%s" % self.ver


class version(object):
    '''
    version object for comparing version numbers.  This also enables special
    strings to be interpreted with special weight values that can be added or
    removed from the version.weights dictionary.
    '''
    weights = {
        'dev': -1100,
        'alpha': -1000,
        'beta': -900,
        'ctp': -900,
        'rc': -800,
        'pc': -800,
        'rtm': -700,
        'gold': -700,
        'release': -700,
        'final': -700,
    }

    __slots__ = ["ver", "parts", "matches"]

    __re = re.compile(r"(\d*)(\D*)(.*)")

    def __init__(self, ver=None, *args):
        '''
        Setup a new version object by copying over from another version, passing
        in a series of items that can be converted to strings, or nothing.  If
        the string version is None or empty, the version number will be treated
        as '0.0.0'.
        '''
        if __debug__:
            logInstanceCreation(self)
        if isinstance(ver, version):
            self.ver = ver.ver
            self.parts = ver.parts[:]
            return

        self.ver = ver
        self.parts = []
        if self.ver:
            self.ver = str(ver)
            for a in args:
                self.ver += ".%s" % str(a)

            self._parseVersion()
        else:
            # empty version strings map to '0.0.0'
            self.parts.extend([0, 0, 0])

    def _parseVersion(self):
        '''
        Do the initial split on dots and either get the integer form or parse
        the sub piece for a list of version information.
        '''
        for sub in self.ver.split('.'):
            try:
                self.parts.append(int(sub))
            except ValueError:
                ret = self._parseSub(sub)
                if len(ret) == 1:
                    self.parts.extend(ret)
                else:
                    self.parts.append(tuple(ret))

    def _parseSub(self, sub):
        '''
        Pull out a list of version parts and integers based on a sub-part of the
        version string.
        '''
        m = self.__re.match(sub)
        if not m:
            # this shouldn't happen, but to be safe
            raise ValueError()

        ret = []
        if m.group(1):
            # first group is always an int
            ret.append(int(m.group(1)))

        if m.group(2):
            # second will be a possible special string
            part = VersionPart(m.group(2))
            if m.group(2).lower() in self.weights:
                part.weight = self.weights[m.group(2).lower()]

            ret.append(part)

        if m.group(3):
            # we recurse to try and decipher the rest
            ret.extend(self._parseSub(m.group(3)))

        return ret

    def _alwaysMatch(self, p1, p2):
        '''
        Pythonic way of checking if either part has the always match flag set.
        This essentially just checks the alwaysMatch flag and returns True if
        either is True.
        '''
        try:
            if p1.alwaysMatch:
                return True
        except AttributeError:
            pass

        try:
            if p2.alwaysMatch:
                return True
        except AttributeError:
            pass

        return False

    def _compareArray(self, arr1, arr2):
        '''
        Compares two lists and recursively dives into sub-lists.  If there is
        ever a match, this will set the matches variable to True and break out.
        This will always return either the first difference between the arrays
        or their last elements.  This fixes a problem with regular list
        comparison and the special weight values.
        '''
        len1 = len(arr1)
        len2 = len(arr2)
        if len1 == 0 or len2 == 0:
            self.matches = True
            return len1, len2

        for i in range(max(len1, len2)):
            # set default as zero in case one list is longer
            num1 = 0
            num2 = 0
            if i < len1:
                num1 = arr1[i]

            if i < len2:
                num2 = arr2[i]

            # handle special matches
            if self._alwaysMatch(num1, num2):
                self.matches = True
                break

            list1 = isinstance(num1, tuple)
            list2 = isinstance(num2, tuple)
            if list1 or list2:
                # if one is a list, make sure the other is too and recurse
                if not list1:
                    num1 = [num1]

                if not list2:
                    num2 = [num2]

                num1, num2 = self._compareArray(num1, num2)

            # first difference makes us stop
            if num1 != num2:
                break

        return (num1, num2)

    def compare(self, rhs, comp):
        '''
        Central compare function that compares the internal parts arrays.  The
        comp function is used to compare the first differnce in the two lists
        unless there was a match.
        '''
        if not isinstance(rhs, version):
            rhs = version(rhs)

        self.matches = False
        num1, num2 = self._compareArray(self.parts, rhs.parts)

        return self.matches or comp(num1, num2)

    def __eq__(self, rhs):
        '''
        Checks for equivalence.
        '''
        return self.compare(rhs, lambda x, y: x == y)

    def __ne__(self, rhs):
        '''
        Checks for not equal.
        '''
        return self.compare(rhs, lambda x, y: x != y)

    def __lt__(self, rhs):
        '''
        Checks for less than.
        '''
        return self.compare(rhs, lambda x, y: x < y)

    def __le__(self, rhs):
        '''
        Checks for less or equal.
        '''
        return self.compare(rhs, lambda x, y: x <= y)

    def __gt__(self, rhs):
        '''
        Checks for greater than.
        '''
        return self.compare(rhs, lambda x, y: x > y)

    def __ge__(self, rhs):
        '''
        Checks for greater or equal.
        '''
        return self.compare(rhs, lambda x, y: x >= y)

    def __sub__(self, rhs):
        '''
        Subtraction operator that produces a version range with this as the
        start.
        '''
        if rhs is None:
            rhs = "*"
        if self < rhs:
            ret = version_range("{0}-{1}".format(self, rhs))
        else:
            ret = version_range("{0}-{1}".format(rhs, self))
        return ret

    def __rsub__(self, lhs):
        '''
        Subtraction operator that produces a version range with this as the
        end.
        '''
        if self < lhs:
            ret = version_range("{0}-{1}".format(self, lhs))
        else:
            ret = version_range("{0}-{1}".format(lhs, self))
        return ret

    def __getitem__(self, key):
        if isinstance(key, slice):
            return ".".join([isinstance(x, tuple) and "".join(map(str, x)) or str(x) for x in self.parts[key]])
        else:
            tmp = self.parts[key]
            return isinstance(tmp, tuple) and "".join(map(str, tmp))or str(tmp)

    def __len__(self):
        ''' Returns the length, or number of "dot" number that are contained in this version'''
        return len(self.parts)

    def __str__(self):
        '''
        Prints the string version.  It basically returns the passed in string.
        '''
        return str(self.ver)

    def __repr__(self):
        '''
        Prints the string version.  It basically returns the passed in string.
        '''
        return "<class {} value={}>".format(self.__class__.__name__, str(self))

    # compatiblity functions.. to remove in forms at least
    def Major(self):
        return self[0]

    def major(self):
        return self[0]

    def Minor(self):
        return self[1]

    def minor(self):
        return self[1]

    def Revision(self):
        return self[2]

    def revision(self):
        return self[2]


class version_range(object):
    '''
    Specifies either a start and end value or a set of version ranges to include
    or exclude.  This can then be used with versions to check if they are in a
    particular range.
    '''

    def __init__(self, range=None):
        '''
        Initialize the internal include and exclude arrays and parse the given
        range.
        '''
        if __debug__:
            logInstanceCreation(self)
        self.range = range
        self.incRight = False
        self.incLeft = True
        self.exclude = False
        self.hasInclude = False
        self.start = self.end = None
        self.ranges = []
        if range:
            if isinstance(range, version):
                self.start = range
            else:
                # remove any whitespace so that the range can be given more
                # naturally
                self.range = "".join(range.split())
                self._parseRanges(self.range)

    def _parseRanges(self, range):
        '''
        Splits up the range based on ',' and adds each to the list of ranges.
        '''
        ranges = range.split(',')
        if len(ranges) == 1:
            self._parseRange(range)
            return

        for r in ranges:
            if not r:
                # ignore empty ranges
                continue

            range = version_range(r)
            if not range.exclude:
                self.hasInclude = True

            self.ranges.append(range)

    def _parseRange(self, range):
        '''
        Parses a range detecting '[' or ']' and '(' or ')' for inclusive and
        exclusive ranges respectively.  It splits on the '-' and assumes that
        the caller supplied them in the proper order.  A check is also done for
        '!' either inside or outside of the opening '(' or '[' to mark the range
        as an exclude range.
        '''
        if not range:
            return

        # check for exclude relationship
        self.exclude = False
        if range[0] == '!':
            self.exclude = True
            range = range[1:]

        # check inclusiveness of range
        # these two checks are highly coupled with their default value
        if range[0] == '(':
            self.incLeft = False

        if range[-1] == ']':
            self.incRight = True

        # trim off the extra notation
        if range[0] in ('(', '['):
            range = range[1:]
        if range[-1] in (')', ']'):
            range = range[:-1]

        # check for exclude again in case they stick it inside the brackets
        if range[0] == '!':
            self.exclude = True
            range = range[1:]

        # split up the range and create the start and end versions
        splits = range.split('-')
        if len(splits) == 1:
            self.start = version(splits[0])
            return

        self.start = version(splits[0])
        self.end = version(splits[1])

    def __contains__(self, item):
        '''
        Checks if an item is contained in this range.  The assumption is that
        item is a version object or can be converted to one.  If the range does
        not have an include or exclude list, we only check start and end.  If
        it does have either list, we make sure that at least one range in the
        include list has the item and that none of the excludes have the item.
        If there are no includes, but there are excludes, we assume anything not
        in the excludes is alright.
        '''
        if not isinstance(item, version):
            item = version(item)

        # if we don't have includes or excludes, just check start and end
        if len(self.ranges) == 0:
            good = True
            if not self.start:
                pass
            elif not self.end:
                good = self.start == item
            else:
                if self.incLeft:
                    good = item >= self.start
                else:
                    good = item > self.start

                if self.incRight:
                    good = good and item <= self.end
                else:
                    good = good and item < self.end

            # being excluded means anything in the range is bad
            if self.exclude:
                return not good
            else:
                return good

        # check the includes
        excluded = False
        included = False
        for r in self.ranges:
            if item in r:
                if r.exclude:
                    if not self.hasInclude:
                        included = True
                else:
                    included = True
            else:
                # not being in an exclude range means that they were in the
                # underlying range, so they must be excluded
                if r.exclude:
                    excluded = True
                    break

        # if there were includes, then it must have been included in one of them
        # we aren't in the range if any range excluded it
        return (not self.hasInclude or included) and not excluded

    def bestVersion(self, list):
        '''
        Finds the best version that is in this range from a list of versions.
        The "best" version is defined as the highest version number in the list.
        '''
        for v in reversed(sorted(list)):
            if v in self:
                return version(v)

        return None

    def __str__(self):
        '''
        Returns the string version of the range.  This is just the passed in
        range string from construction.
        '''
        return str(self.range)


SConsEnvironment.Version = version
SConsEnvironment.VersionRange = version_range

api.register.add_global_parts_object('Version', version)
api.register.add_global_parts_object('VersionRange', version_range)
api.register.add_global_object('Version', version)
api.register.add_global_object('VersionRange', version_range)
