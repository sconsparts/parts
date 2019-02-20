
from __future__ import absolute_import, division, print_function

import os
import os.path

import SCons.Errors
from SCons.Debug import logInstanceCreation

from .variable import Variable

# JK note that this took a little extra to get work to get working as this was
# a translation of a class not a tuple of values


class PathVariable(object):

    def __init__(self, name, help, default, validator=None, value=None, help_group=None):
        '''
        '''
        if __debug__:
            logInstanceCreation(self)
        if validator is None:
            validator = self._PathExists

        if SCons.Util.is_List(name) or SCons.Util.is_Tuple(name):
            help = '{0} ( /path/to/{1} )'.format(help, name[0])
        else:
            help = '{0} ( /path/to/{1} )'.format(help, name)

        super(PathVariable, self).__init__(
            help=help,
            default=default,
            validator=validator,
            converter=None,
            value=value,
            help_group=help_group
        )

    def PathAccept(self, key, val, env):
        """Accepts any path, no checking done."""
        pass

    def PathIsDir(self, key, val, env):
        """Validator to check if Path is a directory."""
        if not os.path.isdir(val):
            if os.path.isfile(val):
                m = 'Directory path for option {0} is a file: {1}'
            else:
                m = 'Directory path for option {0} does not exist: {1}'
            raise SCons.Errors.UserError(m.format(key, val))

    def PathIsDirCreate(self, key, val, env):
        """Validator to check if Path is a directory,
           creating it if it does not exist."""
        if os.path.isfile(val):
            m = 'Path for option {0} is a file, not a directory: {1}'
            raise SCons.Errors.UserError(m.format % (key, val))
        if not os.path.isdir(val):
            os.makedirs(val)

    def PathIsFile(self, key, val, env):
        """validator to check if Path is a file"""
        if not os.path.isfile(val):
            if os.path.isdir(val):
                m = 'File path for option {0} is a directory: {1}'
            else:
                m = 'File path for option {0} does not exist: {1}'
            raise SCons.Errors.UserError(m.format(key, val))

    def PathExists(self, key, val, env):
        """validator to check if Path exists"""
        if not os.path.exists(val):
            m = 'Path for option {0} does not exist: {1}'
            raise SCons.Errors.UserError(m.format(key, val))

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
