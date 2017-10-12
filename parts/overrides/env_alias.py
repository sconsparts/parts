

from .. import glb
from .. import common
from ..core import util
#


def Parts_Alias(self, target, source=[], action=None, **kw):
    try:
        self["PART_SECTION"]  # checks that thsi is a "part" else we don't want to do this
        t = self.subst(target)
        # check that we want to modify this target
        if not t.startswith(self.subst("${PART_SECTION}::")) and not t.startswith("run_utest::"):
            return self._orig_Alias("${{PART_SECTION}}::alias::${{PART_ALIAS}}::{0}".format(target), source, action, **kw)
    except KeyError:
        pass
    return self._orig_Alias(target, source, action, **kw)

from SCons.Script.SConscript import SConsEnvironment
##
# override __setitem__ bind env with bindable objects when set
SConsEnvironment._orig_Alias = SConsEnvironment.Alias
SConsEnvironment.Alias = Parts_Alias


def alias_source_node(name, **kw):

    if isinstance(name, SCons.Node.Node):
        return name

    if glb.pnodes.isKnownNode(name):
        return glb.pnodes.GetNode(name)

    return glb.pnodes.Create(SCons.Node.FS.Entry, name, kw)


import SCons.Environment
import SCons.Node

SCons.Environment.AliasBuilder = SCons.Builder.Builder(action=SCons.Environment.alias_builder,
                                                       target_factory=SCons.Node.Alias.default_ans.Alias,
                                                       source_factory=alias_source_node,
                                                       multi=1,
                                                       is_explicit=None,
                                                       name='AliasBuilder')
