
from enum import IntFlag, IntEnum


class ChangeCheck(IntFlag):
    UNKNOWN = 0
    EXPLICIT_SAME = 1 # same but the scanner did not run
    IMPLICIT_SAME = 2 # same and the scanner did run or this is built/visited
    SAME = 3

    EXPLICIT_DIFF = 4 # different but the scanner did not run
    IMPLICIT_DIFF = 8 # different and the scanner did run
    DIFF = 12

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
