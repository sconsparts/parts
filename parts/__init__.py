'''
This file is what python loads when the user say import parts
This file will import main.py and main will do the rest of work needed
'''
from __future__ import absolute_import, division, print_function

# deal with py2 and py3 import issues
from future import standard_library
standard_library.install_aliases()

import sys

# this tests to see if the script parts is running or if we are loading in SCons.
fname = sys._getframe(1).f_code.co_filename
if fname.endswith("pkg_resources.py") or fname.endswith('pkg_resources/__init__.py'):
    pass
    # print sys._getframe(1).f_code.co_filename
else:
    from parts.main import *
