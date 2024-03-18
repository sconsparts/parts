'''
This file is what python loads when the user say import parts
This file will import main.py and main will do the rest of work needed
'''
import sys
import os
import re
import subprocess

## todo! probably want to expand logic to need to load be able to import SCons vs not
## and calling the engine startup logic

# depending on what is loading we might need to have SCons import-able
# all our script that we will run with be in the form of parts-
# these at the moment do not need scons and are independent of the rest of the Parts code
# to all fast loading of these we check arg[0] to see if this is kind of script we are running
script = True if os.path.basename(sys.argv[0]).startswith("parts-") else False

if not script:
    # so far we are not a script, because of this need to make sure SCons can be imported
    try:
        import SCons    
    except ImportError:
        script = True
        try:
            path = re.search(r'engine path: \[\'([\\\:/\w\.\-]*)',
                            subprocess.check_output("scons --version", shell=True).decode(), re.MULTILINE).groups()[0]
        except subprocess.CalledProcessError:
            path = None

        if path:
            path = os.path.split(path)[0]
            sys.path = [path]+sys.path
            print("Scons found at:", path)
        else:
            print("Scons not found! Did you install it? Is the Python environment setup correctly to see it?")

# at the moment the scripts don't need to start the engine()
if script:
    # Running one of our scripts. Don't load engine. Let script control logic
    pass
else:
    # loading from SConstruct .. run engine
    from parts.main import *
