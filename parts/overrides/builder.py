# this overides the builer call so I can get the file that called the builder.
# this allow be a simple test to see what file to check for changes of build
# context

import SCons.Builder
import sys
from .. import glb

scons_builder=SCons.Builder.Builder

def Part_Builder(**kw):
    glb.build_context_files.add(sys._getframe(1).f_code.co_filename)
    return scons_builder(**kw)

SCons.Builder.Builder=Part_Builder

