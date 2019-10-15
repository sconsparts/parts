"""parts.tools.lipo

Tool-specific initialization for lipo (apple utility for creating universal binaries)

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

import parts.tools.Common
import SCons.Builder

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"


lipoObjectBuilder = SCons.Builder.Builder(
    action='lipo $SOURCES -create -output $TARGET',
    suffix="$OBJSUFFIX",
    src_suffix="$OBJSUFFIX",
    src_builder="Object"
)
lipoProgramBuilder = SCons.Builder.Builder(
    action='lipo $SOURCES -create -output $TARGET',
    src_builder="Program"
)
lipoDylibBuilder = SCons.Builder.Builder(
    action='lipo $SOURCES -create -output $TARGET',
    suffix="$SHLIBSUFFIX",
    src_suffix="$SHLIBPREFIX",
    src_builder="SharedLibrary"
)


def generate(env):
    try:
        bld = env['BUILDERS']['UniversalObject']
    except KeyError:
        bld = lipoObjectBuilder
    env['BUILDERS']['UniversalObject'] = bld

    try:
        bld = env['BUILDERS']['UniversalProgram']
    except KeyError:
        bld = lipoProgramBuilder
    env['BUILDERS']['UniversalProgram'] = bld

    try:
        bld = env['BUILDERS']['UniversalSharedLibrary']
    except KeyError:
        bld = lipoDylibBuilder
    env['BUILDERS']['UniversalSharedLibrary'] = bld

    return


def exists(env):
    return env.Detect('lipo')
