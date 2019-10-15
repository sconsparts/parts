
from __future__ import absolute_import, division, print_function

import parts.common as common
import parts.glb as glb
import SCons.Environment
import SCons.Node
from parts.core import util
from SCons.Script.SConscript import SConsEnvironment


def Parts_Alias(self, target, source=[], action=None, **kw):
    targets = common.make_list(target)
    ret = []
    for target in targets:

        if not util.isAlias(target):
            try:
                self["PART_SECTION"]  # checks that this is a "part" else we don't want to do this
                t = self.subst(target)
                section_str = self.subst("${PART_SECTION}::")
                # check that we want to modify this target
                if not t.startswith(section_str) and not t.startswith("run_utest::") and not t.startswith("build::"):
                    ret += self._orig_Alias("${{PART_SECTION}}::alias::${{PART_ALIAS}}::{0}".format(target), source, action, **kw)
                    continue
            except KeyError:
                pass

        # test for builder
        # there is some race case in which this will be None
        # with advance scanner that create Alias nodes
        # the issue seems to be the we have a path that will set
        # the builder and executor to None/Null instead of "del" the member
        tmp = self.arg2nodes(target, self.ans.Alias)[0]
        try:
            if tmp.builder is None:
                del tmp.builder
                del tmp.executor
        except AttributeError:
            pass

        tmp = self._orig_Alias(target, source, action, **kw)
        ret += tmp
        #ret += self._orig_Alias(target, source, action, **kw)
    return ret


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


SCons.Environment.AliasBuilder = SCons.Builder.Builder(action=SCons.Environment.alias_builder,
                                                       target_factory=SCons.Node.Alias.default_ans.Alias,
                                                       source_factory=alias_source_node,
                                                       multi=1,
                                                       is_explicit=None,
                                                       name='AliasBuilder')
