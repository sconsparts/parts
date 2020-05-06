'''
This file is what python loads when the user say import parts
This file will import main.py and main will do the rest of work needed
'''


# deal with py2 and py3 import issues
from future import standard_library
standard_library.install_aliases()

import sys
import os
import re
import subprocess

try:
    import SCons.Script
    script=False
except ImportError:
    script=True
    try:
        path = re.search(r'engine path: \[\'([\\\:/\w\.\-]*)',subprocess.check_output("scons --version",shell=True).decode(),re.MULTILINE).groups()[0]
    except subprocess.CalledProcessError:
        path = None
    
    if path:
        path = os.path.split(path)[0]
        sys.path = [path]+sys.path
        print("Scons found at:",path)
    else:
        print("Scons not found! Did you install it? Is the Python environment setup correctly to see it?")


if script:
    # Running one of our scripts. Don't load engine. Let script control logic
    pass
else:
    # loading from SConstruct .. run engine
    from parts.main import *
