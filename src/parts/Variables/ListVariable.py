
from __future__ import absolute_import, division, print_function

from builtins import map
from builtins import filter
import SCons.Errors
from .variable import Variable
from parts.common import make_unique

# define converter


def _converter(str_val, raw_val, allowedElems=[], mapdict={}):
    """
    """

    # make the list
    if SCons.Util.is_List(raw_val):
        val = raw_val
    else:
        val = [_f for _f in str_val.split(',') if _f]

    # map values # can't hide this in the class easly because of the map arg
    val = list(map(lambda v, m=mapdict: m.get(v, v), val))

    # test for allowed value is allowed values has a value
    if allowedElems != []:
        # validate if we have bad elements
        notAllowed = list(filter(lambda v, aE=allowedElems: not v in aE, val))
        if notAllowed:
            raise ValueError("Invalid value(s) for option: %s" %
                             ','.join(notAllowed))

    # see if we have duplicate elements
    notAllowed = list(filter(lambda v, lst=val: lst.count(v) > 1, val))
    if notAllowed:
        raise ValueError("Value(s) are entered more then once for option: %s" %
                         ','.join(make_unique(notAllowed)))

    return val


class ListVariable2(Variable):

    def __init__(self, name, help, default=[], names=[], map={}, value=None, help_group=None):
        '''
        '''

        names_str = 'allowed names: %s' % " ".join(names)
        help = '\n    '.join(
            (help, '(comma-separated list of names)', names_str)
        )

        converter = lambda str_val, raw_val, elems=names, m=map: _converter(str_val, raw_val, elems, m)

        super(ListVariable2, self).__init__(
            name,
            help=help,
            default=default,
            validator=None,
            converter=converter,
            value=value,
            help_group=help_group
        )


# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
