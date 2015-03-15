import sys
import os

# It is used only when scripts are invoked from local instance of Parts.
# It is not needed when scripts are installed.
def setup():
    try:
        partsUtilLocalPath = os.path.abspath(os.path.join(os.path.split(__file__)[0], '..'))
    except:
        partsUtilLocalPath = '../'

    sys.path.append(partsUtilLocalPath)
    if not 'PYTHONPATH' in os.environ:
        os.environ['PYTHONPATH'] = partsUtilLocalPath
    else:
        os.environ['PYTHONPATH'] += os.pathsep + partsUtilLocalPath
