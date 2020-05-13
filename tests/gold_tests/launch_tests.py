'''Simple script to start up tests. Will do seimple check to see if autest is on the System.
Otherwise it will install autest system at a user level and run the tests

I will probally replace this later with something smarter...

Assumes you have SCons and Parts installed/setup on the path
'''
import subprocess
import sys

if sys.platform != "win32":
    class WindowsError:
        pass

install = False
# check to see if it already exists
try:
    subprocess.check_call(["autest", "--version"], shell=False)
except WindowsError:
    install = True
except OSError:
    install = True
except subprocess.CalledProcessError:
    install = True

if install:
    if sys.platform == "win32":
        # on windows the user probally does not have there path setup for
        # python --user installs. just install normal (as it probally does not
        # need admin)
        subprocess.call(["pip", "install", "autest"], shell=False)
    else:
        # install it on the system ( user level )        
        if subprocess.call(["pip", "install", "autest", "--user"], shell=False):
            # if that fails ( we are probally in a virtualenv)
            subprocess.call(["pip", "install", "autest"], shell=False)

sys.exit(subprocess.call(["autest"] + sys.argv[1:], shell=False))
