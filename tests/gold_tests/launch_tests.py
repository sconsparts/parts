import subprocess
import sys

if sys.platform == 'win32':
    launcher = "launch_tests.bat"
else:
    launcher = "./launch_tests.sh"

sys.exit(subprocess.call([launcher] + sys.argv[1:], shell=False))
