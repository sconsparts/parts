import variable
import SCons.Errors

__enable_strings = ('1', 'yes', 'true',  'on', 'enable', 'search')
__disable_strings = ('0', 'no',  'false', 'off', 'disable')


class PackageVariable(variable.Variable):

    def __init__(self, name, help, default, searchfunc=None, value=None, help_group=None):
        ''' 
        '''
        help = '\n    '.join(
            (help, '( yes | no | /path/to/%s )' % key))

        def _converter(val):
            """
            """
            lval = val.lower()
            if lval in __enable_strings:
                return True
            if lval in __disable_strings:
                return False
            #raise ValueError("Invalid value for boolean option: %s" % val)
            return val

        def _validator(key, val, env, searchfunc):
            """
            """
            # NOTE!: searchfunc is currenty undocumented and unsupported
            # todo: write validator, check for path
            import os
            if env[key] is True:
                if searchfunc:
                    env[key] = searchfunc(key, val)
            elif env[key] and not os.path.exists(val):
                raise SCons.Errors.UserError(
                    'Path does not exist for option %s: %s' % (key, val))

        super(PackageVariable, self).__init__(
            name,
            help=help,
            default=default,
            validator=lambda k, v, e: _validator(k, v, e, searchfunc),
            converter=_converter,
            value=value,
            help_group=help_group
        )


# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
