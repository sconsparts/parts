
from enum import IntFlag, IntEnum



class GroupLogic(IntEnum):
    NONE = 0
    DEFAULT = TOP = 1
    GROUPED = 2

class FileStyle(IntFlag):
    UNKNOWN = 0
    CLASSIC = 1
    NEW = 2
    MIXED = 3

class LoadState(IntEnum):
    '''
    defines how a given part is loaded ( or to be loaded is set in a ReadState property)
    '''
    NONE = 0  # not loaded
    CACHE = 1  # loaded from cache
    FILE = 2  # loaded from file
