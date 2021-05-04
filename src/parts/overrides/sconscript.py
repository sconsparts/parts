# MIT License
#
# Copyright The SCons Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# import items we need to map with in the global space to not break core SCons logic
from SCons.Script.SConscript import call_stack, Frame, SConscriptReturn, SConscriptNodes, sconscript_chdir, stack_bottom, Main
import SCons.Script

import time
import sys
import os


# this is a basic copy of the source from SCons.Script.SConscript
# with one minor change to not care if the "src_dir" is not under the 
# directory of with the script file are loading from.
# Parts get around the issues that is the core concern in SCons 
# by defining a Variant directory to deal with this mapping of a 
# node that is under the directory with the build file when the
# the directory with Source and the directory with the build file 
# do not match. With Parts this happens when we make a Part extern
# in this way we limit the complication that can happen here as these
# become expected mappings.

# Scons as a Repository feature that might break with this fix. However 
# Parts does not use this at the moment directory. Some testing needs to 
# be done to see what happens here and what general change can happen to make
# SCon core happier in hope we can remove this overide with a patch to SCons.

# Another change that might happen as well is to address the script file with builders
# the logic here is backward compatible. However it might be useful to tie in the updated
# logic for the "extern" feature. This would have code clone for "extern" scm location before 
# the script file is read. The negative to this is that this would make all cloning of extern 
# Scm types linear, which would prevent the use of the Parts -scm-j switch to allow for faster 
# grabbing of sources. However there might still be useful cases for this, example allow a sub-part
# to do this if it was being build. which would enable as part to pull different source location to build itself.
# might be an interesting idea to consider later, or might be a waste of time.

def Parts_SConscript(fs, *files, **kw):
    
    top = fs.Top
    sd = fs.SConstruct_dir.rdir()
    exports = kw.get('exports', [])

    # evaluate each SConscript file
    results = []
    for fn in files:
        call_stack.append(Frame(fs, exports, fn))
        old_sys_path = sys.path
        try:
            SCons.Script.sconscript_reading = SCons.Script.sconscript_reading + 1
            if fn == "-":
                exec(sys.stdin.read(), call_stack[-1].globals)
            else:
                if isinstance(fn, SCons.Node.Node):
                    f = fn
                else:
                    f = fs.File(str(fn))
                _file_ = None
                SConscriptNodes.add(f)

                # Change directory to the top of the source
                # tree to make sure the os's cwd and the cwd of
                # fs match so we can open the SConscript.
                fs.chdir(top, change_os_dir=1)
                if f.rexists():
                    actual = f.rfile()
                    _file_ = open(actual.get_abspath(), "rb")
                elif f.srcnode().rexists():
                    actual = f.srcnode().rfile()
                    _file_ = open(actual.get_abspath(), "rb")
                elif f.has_src_builder():
                    # The SConscript file apparently exists in a source
                    # code management system.  Build it, but then clear
                    # the builder so that it doesn't get built *again*
                    # during the actual build phase.
                    f.build()
                    f.built()
                    f.builder_set(None)
                    if f.exists():
                        _file_ = open(f.get_abspath(), "rb")
                if _file_:
                    # Chdir to the SConscript directory.  Use a path
                    # name relative to the SConstruct file so that if
                    # we're using the -f option, we're essentially
                    # creating a parallel SConscript directory structure
                    # in our local directory tree.
                    #
                    # XXX This is broken for multiple-repository cases
                    # where the SConstruct and SConscript files might be
                    # in different Repositories.  For now, cross that
                    # bridge when someone comes to it.
                    try:
                        src_dir = kw['src_dir']
                    except KeyError:
                        ldir = fs.Dir(f.dir.get_path(sd))
                    else:
                        ldir = fs.Dir(src_dir)
                        # The original code would test that the src directory is under the the build file directory
                        # need to do more testing here to look at the case of the SCons Repositories feature.
                        # This feature in general is a shared directory with sources in it that SCons will look
                        # in for files. If that is not used it is clear that everything works. Need to test 
                        # and show if we can do this with more than one Repository defined.
                        # we remove for now as it break logic that just works on SCons already.
                    try:
                        fs.chdir(ldir, change_os_dir=sconscript_chdir)
                    except OSError:
                        # There was no local directory, so we should be
                        # able to chdir to the Repository directory.
                        # Note that we do this directly, not through
                        # fs.chdir(), because we still need to
                        # interpret the stuff within the SConscript file
                        # relative to where we are logically.
                        fs.chdir(ldir, change_os_dir=0)
                        os.chdir(actual.dir.get_abspath())

                    # Append the SConscript directory to the beginning
                    # of sys.path so Python modules in the SConscript
                    # directory can be easily imported.
                    sys.path = [ f.dir.get_abspath() ] + sys.path

                    # This is the magic line that actually reads up
                    # and executes the stuff in the SConscript file.
                    # The locals for this frame contain the special
                    # bottom-of-the-stack marker so that any
                    # exceptions that occur when processing this
                    # SConscript can base the printed frames at this
                    # level and not show SCons internals as well.
                    call_stack[-1].globals.update({stack_bottom:1})
                    old_file = call_stack[-1].globals.get('__file__')
                    try:
                        del call_stack[-1].globals['__file__']
                    except KeyError:
                        pass
                    try:
                        try:
                            if Main.print_time:
                                time1 = time.time()
                            scriptdata = _file_.read()
                            scriptname = _file_.name
                            _file_.close()
                            exec(compile(scriptdata, scriptname, 'exec'), call_stack[-1].globals)
                        except SConscriptReturn:
                            pass
                    finally:
                        if Main.print_time:
                            time2 = time.time()
                            print('SConscript:%s  took %0.3f ms' % (f.get_abspath(), (time2 - time1) * 1000.0))

                        if old_file is not None:
                            call_stack[-1].globals.update({__file__:old_file})
                else:
                    handle_missing_SConscript(f, kw.get('must_exist', None))

        finally:
            SCons.Script.sconscript_reading = SCons.Script.sconscript_reading - 1
            sys.path = old_sys_path
            frame = call_stack.pop()
            try:
                fs.chdir(frame.prev_dir, change_os_dir=sconscript_chdir)
            except OSError:
                # There was no local directory, so chdir to the
                # Repository directory.  Like above, we do this
                # directly.
                fs.chdir(frame.prev_dir, change_os_dir=0)
                rdir = frame.prev_dir.rdir()
                rdir._create()  # Make sure there's a directory there.
                try:
                    os.chdir(rdir.get_abspath())
                except OSError as e:
                    # We still couldn't chdir there, so raise the error,
                    # but only if actions are being executed.
                    #
                    # If the -n option was used, the directory would *not*
                    # have been created and we should just carry on and
                    # let things muddle through.  This isn't guaranteed
                    # to work if the SConscript files are reading things
                    # from disk (for example), but it should work well
                    # enough for most configurations.
                    if SCons.Action.execute_actions:
                        raise e

            results.append(frame.retval)

    # if we only have one script, don't return a tuple
    if len(results) == 1:
        return results[0]
    else:
        return tuple(results)

scons_SConscript = SCons.Script._SConscript._SConscript

# over write the 
SCons.Script._SConscript._SConscript=Parts_SConscript