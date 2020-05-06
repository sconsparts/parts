


import SCons.Errors

from .variable import Variable


class EnumVariable(Variable):

    def __init__(self, name, help, default, allowed_values, map={}, ignorecase=0, value=None, help_group=None):
        '''
        '''

        def _validator(key, val, env, vals):
            if not val in vals:
                raise SCons.Errors.UserError(
                    'Invalid value for option %s: %s' % (key, val))

        help = '%s (%s)' % (help, '|'.join(allowed_values))

        # define validator
        if ignorecase >= 1:
            def validator(key, val, env): return \
                _validator(key, val.lower(), env, allowed_values)
        else:
            def validator(key, val, env): return \
                _validator(key, val, env, allowed_values)

        # define converter
        if ignorecase == 2:
            def converter(val): return map.get(val.lower(), val).lower()
        elif ignorecase == 1:
            def converter(val): return map.get(val.lower(), val)
        else:
            def converter(val): return map.get(val, val)

        super(EnumVariable, self).__init__(
            name,
            help=help,
            default=default,
            validator=validator,
            converter=converter,
            value=value,
            help_group=help_group
        )


# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
