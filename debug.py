from __future__ import absolute_import, division, print_function
import sys
import re
import subprocess
import os


try:
    path = re.search(r'engine path: \[\'([/\w\.\-]*)',subprocess.check_output(["scons","--version"]).decode(),re.MULTILINE).groups()[0]
except:
    path = None

if path:
    path = os.path.split(path)[0]
    sys.path = [path]+sys.path
    print("Scons found at:",path)
else:
    print("Scons not found! Did you install it? Is the Python environment setup correctly to see it?")

import SCons.Script

SCons.Script.main()

