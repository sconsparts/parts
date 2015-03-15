

#########################################################
### This is the init code that make every start correctly.
###
# import main code
import sys
import glb
import reporter
# start up reporter
glb.rpter=reporter.reporter()

import overrides # init all Scons overides
import engine # get engine

# create the engine
glb.engine=engine.parts_addon()

# load rest of the code
import config
import tool_mapping
import pattern
import version
import filters
import version_info
import poptions,installs
import vcs
import build_section
import parts



### import the pieces
import pieces

if not sys._getframe(2).f_code.co_filename.endswith(".py"):

    # start up logic ... runs during import of the code
    glb.engine.Start() # sets up everything

else:
    import pnode.pnode_manager
    glb.pnodes=pnode.pnode_manager.manager()


# import extra funcion
## this will be viewed as global function to the user in the Sconstruct file
globals().update(glb.globals)

import SCons.Script
SCons.Script.Alias('extract_sources')
