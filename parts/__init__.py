''' 
This file is what python loads when the user say import parts
This file will import main.py and main will do the rest of work needed
'''
import sys
# this tests to see if the script parts is running or if we are loading in SCons.
if sys._getframe(1).f_code.co_filename.endswith("pkg_resources.py"):
    pass
    #print sys._getframe(1).f_code.co_filename
else:
  from main import *
