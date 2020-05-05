
from __future__ import absolute_import, division, print_function

import SCons.Errors

from .variable import Variable

__true_strings = ('y', 'yes', 'true', 't', '1', 'on', 'all')
__false_strings = ('n', 'no', 'false', 'f', '0', 'off', 'none')


class IntVariable(Variable):

    def __init__(self, name, help, default, value=None, help_group=None):
        '''
        '''

        def _converter(str_val):
            """
            """
            try:
                return int(str_val)
            except Exception:
                raise ValueError("Invalid value for Int option: %s" % str_val)

        super(IntVariable, self).__init__(
            help=help,
            default=default,
            validator=None,
            converter=_converter,
            value=value,
            help_group=help_group
        )
