''' 
This file is what python loads when the user say import parts
This file will import main.py and main will do the rest of work needed
'''


from main import *

##__all__ = []
##for subpackage in ['core']:
##    try:
##        exec 'import ' + subpackage
##        __all__.append( subpackage )
##    except ImportError:
##        pass