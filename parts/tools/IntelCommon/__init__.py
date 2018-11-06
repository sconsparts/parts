
from __future__ import absolute_import, division, print_function

# if posix
from . import intelc_posix
# if windows
from . import intelc_win32
from . import intelc_win32_12
from . import intelc_win32_91
from .common import Intelc
