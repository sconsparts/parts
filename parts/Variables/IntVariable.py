
import variable
import SCons.Errors

__true_strings = ('y', 'yes', 'true', 't', '1', 'on', 'all')
__false_strings = ('n', 'no', 'false', 'f', '0', 'off', 'none')


class IntVariable(variable.Variable):

    def __init__(self, name, help, default, value=None, help_group=None):
        ''' 
        '''

        def _converter(str_val):
            """
            """
            try:
                return int(str_val)
            except:
                raise ValueError("Invalid value for Int option: %s" % val)

        super(IntVariable, self).__init__(
            help=help,
            default=default,
            validator=None,
            converter=_converter,
            value=value,
            help_group=help_group
        )


# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
