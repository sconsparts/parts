from __future__ import absolute_import, division, print_function

import linecache
import os
import sys

import parts.glb as glb


class AllowedDuplication(Exception):
    pass


class LoadStoredError(Exception):
    pass


# stuff to help with reporting debug info
def ResetPartStackFrameInfo():
    if len(glb.part_frame) > 0:
        glb.part_frame.pop(0)


def list_endwith(str, lst):
    str = str.lower()
    for l in lst:
        l = l.lower()
        if str.endswith(l):
            return True
    return False


def SetPartStackFrameInfo(use_existing=False):
    # putting tuple of (filename, line, routine, content) into glb.part_frame
    if use_existing == True:
        if len(glb.part_frame) > 0:
            glb.part_frame.insert(0, glb.part_frame[0])
            return

    # We avoid using of inspect.* functions here because
    # the functions are redundant in this case and add
    # additional overhead.

    # The following returns a frame of SetPartStackFrameInfo caller
    # we will use its values as default return data
    frame = sys._getframe(1)
    part_frame = frame
    try:
        checked = False
        while part_frame:
            if not checked:
                # determining best parts source to return
                if not part_frame.f_code.co_filename.endswith('parts' + os.sep + 'errors.py') and\
                        not part_frame.f_code.co_filename.endswith('parts' + os.sep + 'reporter.py') and\
                        not part_frame.f_code.co_filename.endswith(os.sep.join(['parts', 'api', 'output.py'])):
                    frame = part_frame
                    checked = True
            if list_endwith(part_frame.f_code.co_filename, [".parts", ".part", "sconstruct"]):
                break
            part_frame = part_frame.f_back
        else:
            part_frame = frame

        assert(not part_frame is None)
        lineno = part_frame.f_lineno
        line = linecache.getline(part_frame.f_code.co_filename, lineno)
        glb.part_frame.insert(0, (part_frame.f_code.co_filename, lineno, part_frame.f_code.co_name, line))

    finally:
        # We delete frame and part_frame here to avoid leaking refernce to frame
        # such leaks "can cause your program to create reference cycles. Once a
        # reference cycle has been created, the lifespan of all objects which
        # can be accessed from the objects which form the cycle can become much
        # longer even if Python's optional cycle detector is enabled. If such
        # cycles must be created, it is important to ensure they are explicitly
        # broken to avoid the delayed destruction of objects and increased
        # memory consumption which occurs."

        del frame
        del part_frame


# some functions to get the current stack frame of interest for reporting purposes
def GetPartStackFrameInfo():

    if glb.part_frame == []:
        SetPartStackFrameInfo()
        ret = glb.part_frame[0]
        ResetPartStackFrameInfo()
    else:
        ret = glb.part_frame[0]

    if ret is []:
        return ("unknown", "unknown", "unknown", "unknown")
    
    return ret
