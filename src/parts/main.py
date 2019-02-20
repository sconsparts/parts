#########################################################
# This is the init code that make every start correctly.
###
# import main code

from __future__ import absolute_import, division, print_function # isort:skip

import sys                          # isort:skip

import SCons.Script                 # isort:skip

# this has to be the first two import of Parts
import parts.glb as glb             # isort:skip
import parts.reporter as reporter   # isort:skip 
# start up reporter
glb.rpter = reporter.reporter()     # isort:skip

import parts.build_section as build_section
import parts.config as config
import parts.engine as engine  # get engine
import parts.filters as filters
import parts.installs as installs
import parts.overrides  # init all Scons overides
import parts.parts as parts
import parts.pattern as pattern
import parts.poptions as poptions
import parts.tool_mapping as tool_mapping
import parts.vcs as vcs
import parts.version as version
import parts.version_info as version_info

# import the pieces
# this has to be delayed 
import parts.pieces as pieces # isort:skip

# create the engine
glb.engine = engine.parts_addon()


# start up logic ... runs during import of the code
glb.engine.Start()  # sets up everything

# import extra funcion
# this will be viewed as global function to the user in the Sconstruct file
globals().update(glb.globals)

# empty target for checking out vcs logic code only
SCons.Script.Alias('extract_sources')
