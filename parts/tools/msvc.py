"""engine.SCons.Tool.msvc

Tool-specific initialization for Microsoft Visual C/C++.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.

"""

#
# __COPYRIGHT__
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
#

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

import os.path
import re
import string
import sys

import SCons.Action
import SCons.Builder
import SCons.Errors
import SCons.Platform.win32
import SCons.Tool
import SCons.Tool.msvs
import SCons.Util
import SCons.Warnings
import SCons.Scanner.RC

#from MSCommon import msvc_exists,setup_env,is_win64
from parts.tools.MSCommon import msvc, validate_vars

import parts.api.output as output
import parts.tools.Common

CSuffixes = ['.c', '.C']
CXXSuffixes = ['.cc', '.cpp', '.cxx', '.c++', '.C++']


def pch_emitter(target, source, env):
    """Adds the object file target."""

    validate_vars(env)

    pch = None
    obj = None

    for t in target:
        if SCons.Util.splitext(str(t))[1] == '.pch':
            pch = t
        if SCons.Util.splitext(str(t))[1] == '.obj':
            obj = t

    if not obj:
        obj = SCons.Util.splitext(str(pch))[0] + '.obj'

    target = [pch, obj]  # pch must be first, and obj second for the PCHCOM to work

    return (target, source)


def object_emitter(target, source, env, parent_emitter):
    """Sets up the PCH dependencies for an object file."""

    validate_vars(env)

    parent_emitter(target, source, env)

    if env.has_key('PCH') and env['PCH']:
        env.Depends(target, env['PCH'])

    return (target, source)


def static_object_emitter(target, source, env):
    return object_emitter(target, source, env,
                          SCons.Defaults.StaticObjectEmitter)


def shared_object_emitter(target, source, env):
    return object_emitter(target, source, env,
                          SCons.Defaults.SharedObjectEmitter)

pch_action = SCons.Action.Action('$PCHCOM', '$PCHCOMSTR')
pch_builder = SCons.Builder.Builder(action=pch_action, suffix='.pch',
                                    emitter=pch_emitter,
                                    source_scanner=SCons.Tool.SourceFileScanner)


# Logic to build .rc files into .res files (resource files)
res_scanner = SCons.Scanner.RC.RCScan()
res_action = SCons.Action.Action('$RCCOM', '$RCCOMSTR')
res_builder = SCons.Builder.Builder(action=res_action,
                                    src_suffix='.rc',
                                    suffix='.res',
                                    src_builder=[],
                                    source_scanner=res_scanner)


def msvc_batch_key(action, env, target, source):
    """
    Returns a key to identify unique batches of sources for compilation.

    If batching is enabled (via the $MSVC_BATCH setting), then all
    target+source pairs that use the same action, defined by the same
    environment, and have the same target and source directories, will
    be batched.

    Returning None specifies that the specified target+source should not
    be batched with other compilations.
    """
    b = env.subst('$MSVC_BATCH')
    if b in (None, '', '0'):
        # We're not using batching; return no key.
        return None
    t = target[0]
    s = source[0]
    if os.path.splitext(t.name)[0] != os.path.splitext(s.name)[0]:
        # The base names are different, so this *must* be compiled
        # separately; return no key.
        return None
    return (id(action), id(env), t.dir, s.dir)


def msvc_output_flag(target, source, env, for_signature):
    """
    Returns the correct /Fo flag for batching.

    If batching is disabled or there's only one source file, then we
    return an /Fo string that specifies the target explicitly.  Otherwise,
    we return an /Fo string that just specifies the first target's
    directory (where the Visual C/C++ compiler will put the .obj files).
    """
    print "called *************"
    b = env.subst('$MSVC_BATCH')
    if b in (None, '', '0') or len(source) == 1:
        return '/Fo$TARGET'
    else:
        # The Visual C/C++ compiler requires a \ at the end of the /Fo
        # option to indicate an output directory.  We use os.sep here so
        # that the test(s) for this can be run on non-Windows systems
        # without having a hard-coded backslash mess up command-line
        # argument parsing.
        return '/Fo${TARGET.dir}' + os.sep

CAction = SCons.Action.Action("$CCCOM", "$CCCOMSTR",
                              batch_key=msvc_batch_key,
                              targets='$CHANGED_TARGETS')
ShCAction = SCons.Action.Action("$SHCCCOM", "$SHCCCOMSTR",
                                batch_key=msvc_batch_key,
                                targets='$CHANGED_TARGETS')
CXXAction = SCons.Action.Action("$CXXCOM", "$CXXCOMSTR",
                                batch_key=msvc_batch_key,
                                targets='$CHANGED_TARGETS')
ShCXXAction = SCons.Action.Action("$SHCXXCOM", "$SHCXXCOMSTR",
                                  batch_key=msvc_batch_key,
                                  targets='$CHANGED_TARGETS')


def generate(env, version=None, use_script=False, script_args=None, **kw):
    """Add Builders and construction variables for MSVC++ to an Environment."""
    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)

    # TODO(batch):  shouldn't reach in to cmdgen this way; necessary
    # for now to bypass the checks in Builder.DictCmdGenerator.__call__()
    # and allow .cc and .cpp to be compiled in the same command line.
    static_obj.cmdgen.source_ext_match = False
    shared_obj.cmdgen.source_ext_match = False

    for suffix in CSuffixes:
        static_obj.add_action(suffix, CAction)
        shared_obj.add_action(suffix, ShCAction)
        static_obj.add_emitter(suffix, static_object_emitter)
        shared_obj.add_emitter(suffix, shared_object_emitter)

    for suffix in CXXSuffixes:
        static_obj.add_action(suffix, CXXAction)
        shared_obj.add_action(suffix, ShCXXAction)
        static_obj.add_emitter(suffix, static_object_emitter)
        shared_obj.add_emitter(suffix, shared_object_emitter)

    # Set-up ms tools paths for default version
    msvc.MergeShellEnv(env)

    env.SetDefault(CCPDBFLAGS=SCons.Util.CLVar(['${"/Z7" if PDB else ""}']))
    env.SetDefault(CCPCHFLAGS=SCons.Util.CLVar(['${(PCH and "/Yu%s /Fp%s"%(PCHSTOP or "",File(PCH))) or ""}']))
    env.SetDefault(_MSVC_OUTPUT_FLAG=msvc_output_flag)
    env.SetDefault(_CCCOMCOM='$CPPFLAGS $_CPPDEFFLAGS $_CPPINCFLAGS $CCPCHFLAGS $CCPDBFLAGS')
    env['CC'] = parts.tools.Common.toolvar('cl', ('cl',), env=env)
    env.SetDefault(CCFLAGS=SCons.Util.CLVar(''))
    env.SetDefault(CFLAGS=SCons.Util.CLVar(''))
    env.SetDefault(CPPPATH=SCons.Util.CLVar(''))
    env.SetDefault(CCCOM='${TEMPFILE("$CC /Fo$TARGET /c $SOURCES $CFLAGS $CCFLAGS $_CCCOMCOM")}')
    env.SetDefault(SHCC='$CC')
    env.SetDefault(SHCCFLAGS=SCons.Util.CLVar('$CCFLAGS'))
    env.SetDefault(SHCFLAGS=SCons.Util.CLVar('$CFLAGS'))
    env.SetDefault(SHCCCOM='${TEMPFILE("$SHCC $(/Fo$TARGET /c $SOURCES$) $SHCFLAGS $SHCCFLAGS $_CCCOMCOM")}')
    env.SetDefault(CXX='$CC')
    env.SetDefault(CXXFLAGS=SCons.Util.CLVar(''))
    env.SetDefault(CXXCOM='${TEMPFILE("$CXX $(/Fo$TARGET /c $SOURCES$) $CXXFLAGS $CCFLAGS $_CCCOMCOM")}')
    env.SetDefault(SHCXX='$CXX')
    env.SetDefault(SHCXXFLAGS=SCons.Util.CLVar('$CXXFLAGS'))
    env.SetDefault(SHCXXCOM='${TEMPFILE("$SHCXX $(/Fo$TARGET /c $SOURCES$) $SHCXXFLAGS $SHCCFLAGS $_CCCOMCOM")}')
    env.SetDefault(CPPDEFPREFIX='/D')
    env.SetDefault(CPPDEFSUFFIX='')
    env.SetDefault(INCPREFIX='/I')
    env.SetDefault(INCSUFFIX='')

#    env.Append(OBJEMITTER = [static_object_emitter])
#    env.Append(SHOBJEMITTER = [shared_object_emitter])
    env.SetDefault(STATIC_AND_SHARED_OBJECTS_ARE_THE_SAME=1)

    env['RC'] = parts.tools.Common.toolvar('rc', ('rc',), env=env)
    env.SetDefault(RCFLAGS=SCons.Util.CLVar(''))
    env.SetDefault(RCSUFFIXES=['.rc', '.rc2'])
    env.SetDefault(RCCOM="$RC $_CPPDEFFLAGS $_CPPINCFLAGS $RCFLAGS /fo$TARGET $SOURCES")
    env['BUILDERS']['RES'] = res_builder
    env.SetDefault(OBJPREFIX='')
    env.SetDefault(OBJSUFFIX='.obj')
    env.SetDefault(SHOBJPREFIX='$OBJPREFIX')
    env.SetDefault(SHOBJSUFFIX='$OBJSUFFIX')

    env.SetDefault(CFILESUFFIX='.c')
    env.SetDefault(CXXFILESUFFIX='.cc')

    env.SetDefault(PCHPDBFLAGS=SCons.Util.CLVar(['${(PDB and "/Yd") or ""}']))
    env.SetDefault(
        PCHCOM='${TEMPFILE("$CXX /Fo${TARGETS[1]} $CXXFLAGS $CCFLAGS $CPPFLAGS $_CPPDEFFLAGS $_CPPINCFLAGS /c $SOURCES /Yc$PCHSTOP /Fp${TARGETS[0]} $CCPDBFLAGS $PCHPDBFLAGS")}')
    env['BUILDERS']['PCH'] = pch_builder

    # fix this up so we can control its printing to screen better.
    #api.output.print_msg("Configured Tool %s\t for version <%s> target <%s>"%('msvc',env['MSVC']['VERSION'],env['TARGET_PLATFORM']))


def exists(env):
    return msvc.Exists(env)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
