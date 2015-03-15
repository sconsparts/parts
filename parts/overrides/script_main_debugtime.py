'''
We monkey-patch SCons.Script.Main.main() to output debug time even if the build failed for some
obscure exception - it's not clear why SCons wanted to hide this statistics in such a case.

To detect if SCons has already printed the info we also monkey-patch
SCons.Debug.dump_caller_counts which is only called by main() right before printint the stats
'''

import time
import atexit

import SCons.Script
import SCons.Script.Main as Main
import SCons.Debug

def wrapFunction(targetObj, targetAttrName):
    def wrapped(func):
        original = getattr(targetObj, targetAttrName)
        def wrapper(*args, **kw):
            return func(original, *args, **kw)
        setattr(targetObj, targetAttrName, wrapper)
        return wrapper
    return wrapped

SCONS_EXITED_NORMALLY = False
pre_parts_cache_storing = None

def printTimingStatistics():
    if not (SCONS_EXITED_NORMALLY or not Main.print_time):
        # SCons didn't exit normally (that means no printed statistics), and we were
        # requested to output such statistics, so we print it ourselves

        # the below is copy-paste from Main.main() that prints timing stuff
        # the only difference is adding of "Main." before the variables taken
        # from that module
        total_time = (pre_parts_cache_storing or time.time()) - SCons.Script.start_time
        if Main.num_jobs == 1:
            ct = Main.cumulative_command_time
        else:
            if Main.last_command_end is None or Main.first_command_start is None:
                ct = 0.0
            else:
                ct = Main.last_command_end - Main.first_command_start
        scons_time = total_time - Main.sconscript_time - ct
        print "Total build time: %f seconds" % total_time
        print "Total SConscript file execution time: %f seconds" % Main.sconscript_time
        print "Total SCons execution time: %f seconds" % scons_time
        print "Total command execution time: %f seconds" % ct

@wrapFunction(SCons.Debug, 'dump_caller_counts')
def patched_dump_caller_counts(original, *args, **kw):
    '''
    If we got here it means that scons will print time statistics, no need to do so ourselves
    '''
    global SCONS_EXITED_NORMALLY
    SCONS_EXITED_NORMALLY = True
    return original(*args, **kw)

atexit.register(printTimingStatistics)
