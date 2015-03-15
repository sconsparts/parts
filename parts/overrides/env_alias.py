

from .. import glb
from .. import common
#
#def Parts_Alias(self,target, source=[], action=None, **kw):
#    if glb.pnodes.isKnownNode(target):
#        a=glb.pnodes.GetNode(target)
#        if hasattr(a,'builder') and a.builder is None:
#            a.convert()
#    tmp=self._orig_Alias(target,source,action,**kw)
##    glb.pnodes.AddAlias(tmp)
#    return tmp
##
##
#from SCons.Script.SConscript import SConsEnvironment
#
## override __setitem__ bind env with bindable objects when set
#SConsEnvironment._orig_Alias=SConsEnvironment.Alias
#SConsEnvironment.Alias=Parts_Alias


def alias_source_node(name, **kw):

    if isinstance(name, SCons.Node.Node):
        return name

    if glb.pnodes.isKnownNode(name):
        return glb.pnodes.GetNode(name)

    return glb.pnodes.Create(SCons.Node.FS.Entry,name, kw)


import SCons.Environment
import SCons.Node

SCons.Environment.AliasBuilder = SCons.Builder.Builder(action = SCons.Environment.alias_builder,
                                     target_factory = SCons.Node.Alias.default_ans.Alias,
                                     source_factory = alias_source_node,
                                     multi = 1,
                                     is_explicit = None,
                                     name='AliasBuilder')



