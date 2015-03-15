
import variable
import SCons.Errors

_true_strings  = ('y', 'yes', 'true', 't', '1', 'on' , 'all' )
_false_strings = ('n', 'no', 'false', 'f', '0', 'off', 'none')

class BoolVariable(variable.Variable):
    def __init__(self,name, help, default, value=None, help_group=None):
        ''' Create a variable that deal with common boolean values
        
        @param name The name of this variable
        @param help Optional help string
        @param default Optional default value to be used for the variable
        @param value Optional value that is used to set this varibale to a given value
        @param help_group Optional group to be used to help sort the text under
        
        '''
        
        def _text2bool(val):
            """
            Converts strings to True/False depending on the value of the string.
            
            @param val string value to convert
            """
            lval = val.lower()
            if lval in _true_strings: return True
            if lval in _false_strings: return False
            raise ValueError("Invalid value for boolean option: %s" % val)

        def _validator(key, val, env):
            """
            Validates the given value to be either True or False.
            """
            if not env[key] in (True, False):
                raise SCons.Errors.UserError(
                    'Invalid value for boolean option %s: %s' % (key, env[key]))
                    
        super(BoolVariable, self).__init__(
            name,
            help=help,
            default=default,
            validator=_validator, 
            converter=_text2bool,
            value=value,
            help_group=help_group
            )



# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
