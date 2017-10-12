# this set of fixes deal with error handing issues

from SCons.Script import _SConscript
import SCons.Script
import sys
import os

OrigSConscript_exception = _SConscript.SConscript_exception


def PartSConscript_exception(file=None):
    ''' this is silly in general, but is done to allow the remapping of stream 
    to work better as the orginal code get the stream before I remap it as it is
    a default option. This prevents sys.stderr from being used but rather my 
    stderr to be used.'''

    # in case of a early startup issues error
    if file == None:
        file = sys.stderr
    OrigSConscript_exception(file)
_SConscript.SConscript_exception = PartSConscript_exception

import SCons.Script.Main

# overides for better error reporting


def Parts_find_deepest_user_frame(tb):
    """
    Find the deepest stack frame that is not part of SCons.

    Input is a "pre-processed" stack trace in the form
    returned by traceback.extract_tb() or traceback.extract_stack()
    """

    tb.reverse()

    # find the deepest traceback frame that is not part
    # of SCons:
    ftmp = SCons.Script.GetOption("file")
    if len(ftmp) == 0:
        ftmp = ['sconstruct']

    def list_endwith(str, lst):
        str = str.lower()
        for l in lst:
            l = l.lower()
            if str.endswith(l):
                return True
        return False
    # print len(tb)
    for frame in tb:
        filename = frame[0]
        # print filename
        if filename.find(os.sep + 'SCons' + os.sep) == -1 and list_endwith(filename, ['.parts', '.part']) == True:
            return frame
        elif list_endwith(filename, ftmp):
            return lastframe
        lastframe = frame
    # print "->",tb[0]
    return tb[0]

SCons.Script.Main.find_deepest_user_frame = Parts_find_deepest_user_frame
