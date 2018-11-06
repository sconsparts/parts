"""SCons.Tool.masm

Tool-specific initialization for the Microsoft Assembler.

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
from __future__ import absolute_import, division, print_function

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

import parts.api.output as output
import parts.tools.Common
from parts.tools.MSCommon import is_win64, msvc

import SCons.Defaults
import SCons.Tool
import SCons.Util

ASSuffixes = ['.s', '.asm', '.ASM']
ASPPSuffixes = ['.spp', '.SPP', '.sx']
if SCons.Util.case_sensitive_suffixes('.s', '.S'):
    ASPPSuffixes.extend(['.S'])
else:
    ASSuffixes.extend(['.S'])


def generate(env):
    """Add Builders and construction variables for masm to an Environment."""
    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)

    for suffix in ASSuffixes:
        static_obj.add_action(suffix, SCons.Defaults.ASAction)
        shared_obj.add_action(suffix, SCons.Defaults.ASAction)
        static_obj.add_emitter(suffix, SCons.Defaults.StaticObjectEmitter)
        shared_obj.add_emitter(suffix, SCons.Defaults.SharedObjectEmitter)

    for suffix in ASPPSuffixes:
        static_obj.add_action(suffix, SCons.Defaults.ASPPAction)
        shared_obj.add_action(suffix, SCons.Defaults.ASPPAction)
        static_obj.add_emitter(suffix, SCons.Defaults.StaticObjectEmitter)
        shared_obj.add_emitter(suffix, SCons.Defaults.SharedObjectEmitter)

    msvc.MergeShellEnv(env)
    if env['TARGET_PLATFORM'] == 'x86_64':
        env['AS'] = parts.tools.Common.toolvar('ml64', ('ml64',), env=env)
    else:
        env['AS'] = parts.tools.Common.toolvar('ml', ('ml',), env=env)
    env['ASFLAGS'] = SCons.Util.CLVar('/nologo')
    env['ASPPFLAGS'] = '$ASFLAGS'
    env['ASCOM'] = '$AS $ASFLAGS /c /Fo$TARGET $SOURCES'
    env['ASPPCOM'] = '$CC $ASPPFLAGS $CPPFLAGS $_CPPDEFFLAGS $_CPPINCFLAGS /c /Fo$TARGET $SOURCES'
    env['STATIC_AND_SHARED_OBJECTS_ARE_THE_SAME'] = 1
    #api.output.print_msg("Configured Tool %s\t for version <%s> target <%s>"%('masm\ml',env['MSVC']['VERSION'],env['TARGET_PLATFORM']))


def exists(env):
    ret = False
    if is_win64():
        ret = msvc.Exists(env, 'ml64')
    else:
        ret = msvc.Exists(env, 'ml')
    return ret

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
