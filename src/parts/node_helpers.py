'''
this file provides the AbsFile wrappers. I have not moved this to pieces area
yet as i need a way to safely add the global object to parts export statement
'''

import SCons.Node.FS
import SCons.Script
from SCons.Debug import logInstanceCreation
# import the meta object we will need to add our code to as methods
from SCons.Script.SConscript import SConsEnvironment

import parts.api as api
import parts.common as common
import parts.glb as glb
import parts.core.util as util
from parts.core.states import ChangeCheck

# this is the decider function map.. need to call decider logic via this map
# of functions

decider_map = SCons.Node._decider_map


class ninfotmp:

    def __init__(self):
        if __debug__:
            logInstanceCreation(self)
        self.timestamp = 0
        self.csig = 0


def build_info_changed(self, scan: bool = True, skip_implicit: bool = True, indent: int = 0) -> ChangeCheck:
    '''
    scan - do we need scan for the to get implicit values defined
    skip_implicit - do we check the implicit value
    '''
    api.output.verbose_msgf(
        ["binfo.change", "node.change"],
        "{indent} Checking binfo for {node}", node=self.ID, indent=' '*(indent+6)
    )
    try:
        # if the node was cached with not changed or it is built
        # this mean we can stop and say it is not changed
        if (self.attributes._has_changed & ChangeCheck.IMPLICIT_SAME) or\
            (skip_implicit and self.attributes._has_changed & ChangeCheck.EXPLICIT_SAME) or\
            (skip_implicit and self.attributes._has_changed & ChangeCheck.EXPLICIT_DIFF) or\
                (not skip_implicit and self.attributes._has_changed & ChangeCheck.IMPLICIT_DIFF):
            api.output.verbose_msgf(
                ["binfo.change", "node.change", "cached"],
                "{indent}{node} Cached: {val}", node=self.ID, val=self.attributes._binfo_changed, indent=' '*(indent+6)
            )
            return self.attributes._has_changed

    except AttributeError as e:
        pass

    # if the node is build or visited it cannot be viewed as changed anymore
    if self.isBuilt or self.isVisited:
        api.output.verbose_msgf(
            ["binfo.change", "node.change"],
            "{indent}{node} has been built!", node=self.ID, indent=' '*(indent+6)
        )
        self.attributes._binfo_changed = ChangeCheck.SAME
        return self.attributes._binfo_changed

    # check that the node exists
    # this is where we may want to look at the ninfo..
    # as if it change then the binfo that creates this would
    # be out of sync.. however at the moment SCons does not see this
    if not self.exists():
        api.output.verbose_msgf(
            ["binfo.change.true", "binfo.change", "node.change.true", "node.change"],
            "{indent}{node} does not exist!", node=self.ID, indent=' '*(indent+1)
        )
        self.attributes._binfo_changed = ChangeCheck.DIFF
        return self.attributes._binfo_changed

    # the node has to have a builder else it is unchanged as it is source to some other target
    # which will have binfo to do a real check if the node needs to be rebuilt
    if not self.has_builder():
        api.output.verbose_msgf(
            ["binfo.change.false", "binfo.change", "node.change.false", "node.change"],
            f"{' '*(indent-1)}{self.ID} is not buildable!",
        )
        self.attributes._binfo_changed = ChangeCheck.SAME
        return self.attributes._binfo_changed

    # then we need to have stored information else this is viewed as changed
    if self.has_stored_info():
        info = self.get_stored_info()
        binfo = info.binfo

        # these are all the children we have in the binfo cache
        if skip_implicit:
            # we might have implicit already..
            children = self.sources + self.depends
            cached_sigs = binfo.bsourcesigs + binfo.bdependsigs
        else:
            children = self.children(scan=scan)
            #children = self.sources + self.depends + self.implicit
            cached_sigs = binfo.bsourcesigs + binfo.bdependsigs + binfo.bimplicitsigs

        # check to see if the defined explicits value differ from the the number of nodes that are defined
        # Known bug here is if depend and sources share a node (Fix this. need to provide issue for SCons)
        diff = len(children) - len(cached_sigs)

        # the children and cached children mismatch
        if diff:
            api.output.verbose_msgf(
                ["binfo.change.true", "binfo.change", "node.change.true", "node.change"],
                "{indent}Sources changed for {node} changed!", node=self.ID, indent=' '*(indent+1))
            if skip_implicit:
                cached_children = binfo.bsources + binfo.bdepends
            else:
                cached_children = binfo.bsources + binfo.bdepends + binfo.bimplicit

            for c in children:
                if c not in cached_children:
                    api.output.verbose_msgf(
                        ["binfo.change.true", "binfo.change", "node.change.true", "node.change"],
                        "{indent} {node} was not found in binfo cache", node=c.ID, indent=' '*(indent+1))
            for c in cached_children:
                if c not in children:
                    if not skip_implicit and c in binfo.bimplicit:
                        dtype = "Implicit"
                    elif c in binfo.bsources:
                        dtype = "Source"
                    elif c in binfo.bdepends:
                        dtype = "Depends"
                    
                    api.output.verbose_msgf(
                        ["binfo.change.true", "binfo.change", "node.change.true", "node.change"],
                        "{indent} {dtype} {node} was in binfo cache but not defined in the node", node=c.ID, indent=' '*(indent+1), dtype=dtype)
            self.attributes._binfo_changed = ChangeCheck.EXPLICIT_DIFF if skip_implicit else ChangeCheck.DIFF
            return self.attributes._binfo_changed

        # check the decider logic if the node changed
        result = ChangeCheck.EXPLICIT_SAME if skip_implicit else ChangeCheck.SAME

        for child, prev_ni in zip(children, cached_sigs):
            # do a decider/sig check if the node it out of date
            # if it fails ... it mean the node change because the child use to build this
            # node is different. It does not mean the logic to build the child changed
            if decider_map[self.changed_since_last_build](child, self, prev_ni, self):

                api.output.verbose_msgf(
                    ["binfo.change.true", "binfo.change", "node.change.true", "node.change"],
                    "{indent}{node} dependent '{child}' changed!", node=self.ID, child=child, indent=' '*(indent+1))
                result = ChangeCheck.EXPLICIT_DIFF if skip_implicit else ChangeCheck.DIFF
                break

        # check the action csig for change
        if not skip_implicit and result & ChangeCheck.SAME and self.action_changed(indent=indent+1):
            api.output.verbose_msgf(
                ["binfo.change.true", "binfo.change", "node.change.true", "node.change"],
                "{indent}{node} action changed!", node=self.ID, child=child, indent=' '*(indent+1))
            result = ChangeCheck.DIFF

    else:
        api.output.verbose_msgf(
            ["binfo.change.true", "binfo.change", "node.change.true", "node.change"],
            "{indent}{node} has no stored info: changed!", node=self.ID, indent=' '*(indent+1))
        result = ChangeCheck.DIFF
    self.attributes._binfo_changed = result
    return self.attributes._binfo_changed


# def node_explicit_change(self, binfo=None, indent=0):
#     '''
#     Check explicit state based on what was is defined in the node
#     checks that the node change based on cached state. This want to return as fast as it can
#     So first change allows us to return result as soon as it is known
#     '''
#     # if the node is build or visited it cannot be viewed as changed anymore
#     if self.isBuilt or self.isVisited:
#         return False
#     # the node has to have a builder else it is unchanged as it is source to some other target
#     # which will have binfo to do a real check if the node needs to be rebuilt
#     if not self.has_builder():
#         return False

#     # then we need to have stored information else this is viewed as changed
#     if not binfo:
#         if not self.has_stored_info():
#             return True
#         info = self.get_stored_info()
#         binfo = info.binfo

#     # the known children to check. This includes sources and explicit depends.
#     # the implicit has to be filed in via a scan we we want to delay
#     children = (self.sources if self.sources else []) + \
#         (self.depends if self.depends else [])

#     cached_sigs = binfo.bsourcesigs + binfo.bdependsigs

#     # check to see if the defined explicits value differ from the the number of nodes that are defined
#     # Known bug here is if depend and sources share a node (Fix this. need to provide issue for SCons)
#     diff = len(children) - len(cached_sigs)
#     if diff:
#         api.output.verbose_msgf(
#             ["node.explicit.change.true", "node.explicit.change", "node.change.true", "node.change"],
#             "{indent}Explicit sources changed for {node} changed!", node=self.ID, indent=" "*indent)
#         return True

#     # this has to be depth first to ensure that dynamic cases are touched correctly
#     # however we can cache results to help speed up the checks.
#     for child, prev_ni in zip(children, cached_sigs):
#         # do a decider/sig check if the node it out of date
#         # if it fails ... it mean the node change because the child use to build this
#         # node is different. It does not mean the logic to build the child changed
#         if decider_map[child.changed_since_last_build](child, self, prev_ni, self):
#             api.output.verbose_msgf(
#                 ["node.explicit.change.true", "node.explicit.change", "node.change.true", "node.change"],
#                 "{indent}{node} dependent '{child}' changed!", node=self.ID, child=child, indent=" "*indent
#             )
#             return True

#     return False


# def node_cached_explicit_change(self, binfo=None, indent=0):
#     '''
#     Check explicit state based on what was stored in cache
#     checks that the node change based on cached state. This want to return as fast as it can
#     So first change allows us to return result as soon as it is known
#     '''

#     # the node has to have a builder else it is unchanged as it is source to some other target
#     # which will have binfo to do a real check if the node needs to be rebuilt
#     if not self.has_builder():
#         return False

#     # then we need to have stored information else this is viewed as changed
#     if not binfo:
#         if not self.has_stored_info():
#             return True
#         info = self.get_stored_info()
#         binfo = info.binfo

#     # The cached explicit children
#     cached_children = binfo.bsources + binfo.bdepends

#     cached_sigs = binfo.bsourcesigs + binfo.bdependsigs

#     # check to see if the defined explicits value differ from the the number of nodes that are defined
#     # Known bug here is if depend and sources share a node (Fix this. need to provide issue for SCons)
#     diff = len(cached_children) - len(cached_sigs)
#     if diff:
#         api.output.verbose_msgf(
#             ["node.change"], "{indent}Explicit sources changed for {node} changed!", node=self.ID, indent=' '*(indent+6))
#         return True

#     # this has to be depth first to ensure that dynamic cases are touched correctly
#     # however we can cache results to help speed up the checks.
#     for child, prev_ni in zip(cached_children, cached_sigs):
#         # do a decider/sig check if the node it out of date
#         # if it fails ... it mean the node change because the child use to build this
#         # node is different. It does not mean the logic to build the child changed

#         if decider_map[child.changed_since_last_build](child, self, prev_ni):
#             api.output.verbose_msgf(
#                 ["node.change"],
#                 "{indent}Dependent changed {node} changed!", node=self.ID, indent=' '*(indent+6)
#             )
#             return True

#     return False


# def node_cached_implicit_change(self, binfo=None, indent=0):
#     '''
#     Check implicit state based on what was stored in cache
#     checks that the node change based on cached state. This want to return as fast as it can
#     So first change allows us to return result as soon as it is known
#     '''

#     # the node has to have a builder else it is unchanged as it is source to some other target
#     # which will have binfo to do a real check if the node needs to be rebuilt
#     if not self.has_builder():
#         return False

#     # then we need to have stored information else this is viewed as changed
#     if not binfo:
#         if not self.has_stored_info():
#             return True
#         info = self.get_stored_info()
#         binfo = info.binfo

#     # the known children to check. This includes sources and explicit depends.
#     # the implicit has to be filed in via a scan we we want to delay
#     children = binfo.bimplicit
#     cached_sigs = binfo.bimplicitsigs

#     # this has to be depth first to ensure that dynamic cases are touched correctly
#     # however we can cache results to help speed up the checks.
#     for child, prev_ni in zip(children, cached_sigs):
#         # do a decider/sig check if the node it out of date
#         # if it fails ... it mean the node change because the child use to build this
#         # node is different. It does not mean the logic to build the child changed

#         if decider_map[child.changed_since_last_build](child, self, prev_ni, self):
#             api.output.verbose_msgf(
#                 ["node.change"],
#                 "{indent}Dependent changed {node} changed!", node=self.ID, indent=' '*(indent+6)
#             )
#             return True

#     return False


# def node_implicit_change(self, scan=True, binfo=None, indent=0):
#     '''
#     Check the node implicit state by doing a scan() on the node
#     '''

#     # if the node is build or visited it cannot be viewed as changed anymore
#     if self.isBuilt or self.isVisited:
#         return False

#     # the node has to have a builder else it is unchanged as it is source to some other target
#     # which will have binfo to do a real check if the node needs to be rebuilt
#     if not self.has_builder():
#         return False

#     # then we need to have stored information else this is viewed as changed
#     if not binfo:
#         if not self.has_stored_info():
#             return True
#         info = self.get_stored_info()
#         binfo = info.binfo

#     if scan:
#         self.scan()

#     # the known children to check. This includes sources and explicit depends.
#     # the implicit has to be filed in via a scan we we want to delay
#     children = self.implicit
#     cached_sigs = binfo.bimplicitsigs

#     # check to see if the defined explicits value differ from the the number of nodes that are defined
#     # Known bug here is if depend and sources share a node (Fix this. need to provide issue for SCons)
#     diff = len(children) - len(cached_sigs)
#     if diff:
#         api.output.verbose_msgf(
#             ["node.change"],
#             "{indent}Implict sources changed for {node} changed!", node=self.ID, indent=' '*(indent+6)
#         )
#         return True

#     # this has to be depth first to ensure that dynamic cases are touched correctly
#     # however we can cache results to help speed up the checks.
#     for child, prev_ni in zip(children, cached_sigs):
#         # do a decider/sig check if the node it out of date
#         # if it fails ... it mean the node change because the child use to build this
#         # node is different. It does not mean the logic to build the child changed

#         if decider_map[child.changed_since_last_build](child, self, prev_ni, self):
#             api.output.verbose_msgf(
#                 ["node.change"], "{indent}Dependent changed {node} changed!", node=self.ID, indent=' '*(indent+6)
#             )
#             return True

#     return False


# def explicit_change(node, indent=0):
#     '''
#     Check the explicit children (sources and depends)
#     Check is based on defined values via there binfo
#     Does not check the implicit
#     '''

#     # if the node is build or visited it cannot be viewed as changed anymore
#     if node.isBuilt or node.isVisited:
#         return False

#     # the node has to have a builder else it is unchanged as it is source to some other target
#     # which will have binfo to do a real check if the node needs to be rebuilt
#     if not node.is_buildable():
#         return False

#     # if info is none this is the default result
#     result = True
#     if node.has_stored_info():
#         # then we need to have stored information else this is viewed as changed
#         info = node.get_stored_info()
#         # we have info so the default is False now
#         result = False
#         binfo = info.binfo
#         # the known children to check. This includes sources and explicit depends.
#         # the implicit has to be filed in via a scan we we want to delay
#         children = (node.sources if node.sources else []) + \
#             (node.depends if node.depends else [])

#         # this has to be depth first to ensure that dynamic cases are touched correctly
#         # however we can cache results to help speed up the checks.
#         for child in children:
#             # call the child first as we need to go down to the bottom first and then come back up
#             result = explicit_change(child, indent+1)
#         if not result:
#             # given the children did not change we want to make sure our view of the
#             # children did not change
#             result = node_explicit_change(node, binfo=binfo, indent=indent)

#     return result


# def cached_explicit_change(node, indent=0):
#     '''
#     Check the explicit children (sources and depends)
#     Check is based on defined values via there binfo
#     Does not check the implicit
#     '''

#     # the node has to have a builder else it is unchanged as it is source to some other target
#     # which will have binfo to do a real check if the node needs to be rebuilt
#     if not node.is_buildable():
#         return False

#     # if info is none this is the default result
#     result = True
#     if node.has_stored_info():
#         # then we need to have stored information else this is viewed as changed
#         info = node.get_stored_info()
#         # we have info so the default is False now
#         result = False
#         binfo = info.binfo
#         # the known children to check. This includes sources and explicit depends.
#         # the implicit has to be filed in via a scan we we want to delay

#         children = binfo.bsources + binfo.bdepends

#         # this has to be depth first to ensure that dynamic cases are touched correctly
#         # however we can cache results to help speed up the checks.
#         for child in children:
#             # call the child first as we need to go down to the bottom first and then come back up
#             result = cached_explicit_change(child, indent+1)
#         if not result:
#             # given the children did not change we want to make sure our view of the
#             # children did not change
#             result = node_cached_explicit_change(node, binfo=binfo, indent=indent)

#     return result

# not used at the moment
# def implicit_change(node, scan=False, indent=0):
#     '''
#     Check the explicit children (sources and depends)
#     Check is based on defined values via there binfo
#     Does not check the implicit
#     scan controls if this level will use cached implicit or not
#     The recursive call is alway to scan
#     '''
#     api.output.verbose_msgf(
#         ["implicit.change", "node.change"], "{indent}Checking {node}", node=node.ID, indent=" "*indent
#     )
#     # if the node is build or visited it cannot be viewed as changed anymore
#     if node.isBuilt or node.isVisited:
#         return ChangeCheck.UNCHANGED
#     # the node has to have a builder else it is unchanged as it is source to some other target
#     # which will have binfo to do a real check if the node needs to be rebuilt
#     if not node.is_buildable():
#         return ChangeCheck.UNCHANGED

#     # in case this is a directory node
#     if node.builder is SCons.Node.FS.MkdirBuilder and node.exists():
#         return ChangeCheck.UNCHANGED

#     # if info is none this is the default result
#     result = True
#     if node.has_stored_info():
#         # then we need to have stored information else this is viewed as changed
#         info = node.get_stored_info()
#         # we have info so the default is False now
#         result = ChangeCheck.UNCHANGED
#         binfo = info.binfo

#         if scan:
#             api.output.verbose_msgf(
#                 ["implicit.change", "node.change"], "{indent}Scanning {node}", node=node.ID, indent=" "*indent
#             )
#             node.scan()
#             # the known children to check. This includes sources and explicit depends.
#             # the implicit has to be filed in via a scan we we want to delay
#             children = (node.implicit if node.implicit else [])
#         else:
#             children = binfo.bimplicit
#         api.output.verbose_msgf(
#             ["implicit.change", "node.change"],
#             "{indent}implicit {children}", children=common.DelayVariable(lambda: [n.ID for n in children]), indent=" "*indent
#         )
#         # this has to be depth first to ensure that dynamic cases are touched correctly
#         # however we can cache results to help speed up the checks.
#         for child in children:
#             # call the child first as we need to go down to the bottom first and then come back up
#             result = implicit_change(child, scan=True, indent=indent+1)
#         if not result:
#             # given the children did not change we want to make sure our view of the
#             # children did not change
#             if scan:
#                 # we already scanned.. so don't redo the scan again
#                 result = node_implicit_change(node, scan=False, binfo=binfo, indent=indent)
#             else:
#                 result = node_cached_implicit_change(node, binfo=binfo, indent=indent)

#     return result

# no used a the moment..
# def cached_implicit_change(node, indent=0):
#     '''
#     Check the explicit children (sources and depends)
#     Check is based on defined values via there binfo
#     Does not check the implicit
#     scan controls if this level will use cached implicit or not
#     The recursive call is alway to scan
#     '''
#     if not util.isNode(node):
#         api.output.error_msg(f"cached_implicit_change node argument is not a Scons.node type. Type passed in {type(node)}")
#     # the node has to have a builder else it is unchanged as it is source to some other target
#     # which will have binfo to do a real check if the node needs to be rebuilt
#     if not node.is_buildable():
#         return ChangeCheck.UNCHANGED

#     # then we need to have stored information else this is viewed as changed
#     info = node.get_stored_info()

#     # if info is none this is the default result
#     result = True
#     if info:
#         # we have info so the default is False now
#         result = ChangeCheck.UNCHANGED
#         binfo = info.binfo

#         children = binfo.bimplicit

#         # this has to be depth first to ensure that dynamic cases are touched correctly
#         # however we can cache results to help speed up the checks.
#         for child in children:
#             # call the child first as we need to go down to the bottom first and then come back up
#             result = cached_implicit_change(child, indent=indent+1)
#         if not result:
#             # given the children did not change we want to make sure our view of the
#             # children did not change
#             result = node_cached_explicit_change(node, binfo=binfo, indent=indent)

#     return result


def has_changed(node, skip_implicit: bool = False, indent: int = 0) -> ChangeCheck:
    '''
    This function tries to tell if the node changes. This differs from the SCons
    function up_to_date/changed (which are optimized for the task logic) in two ways:
    1) It tries to find if something is different and exits as quick as possible.
        a. only exception at the moment is we do the children size check later.
    2) It check explicit depend before calling scanners to get implicit depends

    This should avoid some unneeded scans and checks when out of date.
    The logic also does this depth first. this is to ensure better
    environment state in cases of scanner calling builders.

    skip_implicit - allows us to skip testing this nodes implicit as we maybe testing
    this in the scanner for this node ( so the implicit are not known yet)

    '''
    # because node list are easy to pass we need to validate this is a node not a list.
    if not util.isNode(node):
        api.output.error_msg(f"has_change node argument is not a Scons.node type. Type passed in {type(node)}")
    if indent == 0:
        api.output.verbose_msg(["node.change"], "----------------------------------------")
    api.output.verbose_msgf(["node.change"], f"{' '*(indent+6)}checking has_changed {node.ID}, {id(node)}")

    # if the node is build or visited it cannot be viewed as changed anymore
    if node.isBuilt or node.isVisited:
        api.output.verbose_msgf(
            ["node.change.false", "node.change"],
            "{indent}{node} has been built!", node=node.ID, indent=' '*indent)
        node.attributes._has_changed = ChangeCheck.IMPLICIT_SAME
        return ChangeCheck.IMPLICIT_SAME

    try:
        # if the node was cached with not changed or it is built
        # this mean we can stop and say it is not changed

        if node.attributes._has_changed & ChangeCheck.IMPLICIT_SAME:
            api.output.verbose_msgf(
                ["node.change.false", "node.change", "cached"],
                f"{' '*indent}{node.ID} Cached: {node.attributes._has_changed}"
            )
            return node.attributes._has_changed
        elif skip_implicit and node.attributes._has_changed & ChangeCheck.EXPLICIT_SAME:
            api.output.verbose_msgf(
                ["node.change.false", "node.change", "cached"],
                f"{' '*indent}{node.ID} Cached: {node.attributes._has_changed}"
            )
            return node.attributes._has_changed
        # if skip implicit and we at
        elif skip_implicit and node.attributes._has_changed & ChangeCheck.EXPLICIT_DIFF:
            api.output.verbose_msgf(
                ["node.change.true", "node.change", "cached"],
                f"{' '*indent}{node.ID} Cached: {node.attributes._has_changed}"
            )
            return node.attributes._has_changed
        elif not skip_implicit and node.attributes._has_changed & ChangeCheck.IMPLICIT_DIFF:
            api.output.verbose_msgf(
                ["node.change.true", "node.change", "cached"],
                f"{' '*indent}{node.ID} Cached: {node.attributes._has_changed}"
            )
            return node.attributes._has_changed

    except AttributeError as e:
        pass

    # the node has to have a builder else it is unchanged as it is source to some other target
    # Only targets have builders and the binfo to check for differences
    if not node.is_buildable():
        api.output.verbose_msg(
            ["node.change.false", "node.change"],
            f'{" "*indent}{node.ID} has no builder'
        )
        node.attributes._has_changed = ChangeCheck.SAME  # does not matter if we scan or not
        return node.attributes._has_changed

    # if info is none this is the default result
    result = ChangeCheck.EXPLICIT_DIFF if skip_implicit else ChangeCheck.DIFF
    if node.has_stored_info():
        # we have info so the default is False now
        result = ChangeCheck.EXPLICIT_SAME if skip_implicit else ChangeCheck.SAME

        ###################################################
        # we have to scan at this point to make sure all environmental additions
        # at added. It would be nice if we have a way to add a node that had to be
        # processed first like a prerequisites that did not effect the depends or action
        # and would be stored in the cache so we knew to process these first to make sure
        # the incremental build would be correctly. This would allow us to delay scanning
        # until it was needed for an updated check.

        children = node.children(scan=not skip_implicit)
        api.output.verbose_msgf(
            ["node.change"],
            f'{" "*(indent+6)}{node.ID} - Checking {len(children)} children.'
        )
        # now we want to check the children to see if they changed ( if they did we changed as well)
        for child in children:
            # skip children with no builder
            if not child.has_builder():
                api.output.verbose_msgf(
                    ["node.change"],
                    f"{' '*(indent+7)}{child.ID} Skipping.. No builder!.",
                )
                continue

            # call the child first as we need to go down to the bottom first and then come back up
            result = has_changed(child, skip_implicit=skip_implicit, indent=indent+2)
            if result & ChangeCheck.DIFF:
                api.output.verbose_msgf(
                    ["node.change.true", "node.change"],
                    f"{' '*(indent+1)}{node.ID} changed because of child {child.ID}.",
                )
                break
        # check build info
        if result & ChangeCheck.SAME:
            # given the children did not change we want to make sure our view of the
            # children did not change
            # don't need to scan again
            result = build_info_changed(node, scan=False, skip_implicit=skip_implicit, indent=(indent+1))
            if result & ChangeCheck.DIFF:
                api.output.verbose_msgf(
                    ["node.change.true", "node.change"],
                    "{indent}{node} changed!.", node=node.ID, indent=' '*(indent+1)
                )

    else:
        api.output.verbose_msgf(
            ["node.change.true", "node.change"],
            "{indent}{node} has no stored info: changed!", node=node.ID, indent=' '*(indent+1)
        )
        result = ChangeCheck.IMPLICIT_DIFF

    node.attributes._has_changed = result
    if result & ChangeCheck.SAME:
        api.output.verbose_msgf(["node.change.false", "node.change"],
                                "{indent}{node} did not change.", node=node.ID, indent=" "*indent)

    api.output.verbose_msgf(
        ["node.change"],
        "{indent}{node} returned. {c}", node.attributes._has_changed, node=node.ID, indent=" "*(indent+6), c=node.attributes._has_changed
    )
    return node.attributes._has_changed


def has_children_changed(node, indent=0) -> ChangeCheck:
    '''
    Like has_changed expect that we only care if the depends and sources need to be updated
    given that this node probally needs to be updated still
    '''

    # because node list are easy to pass we need to validate this is a node not a list.
    if not util.isNode(node):
        api.output.error_msg(f"has_children_changed node argument is not a Scons.node type. Type passed in {type(node)}")

    api.output.verbose_msgf(["node.change"], "{indent}checking children {node}", node=node.ID, indent=' '*(indent+6))

    # the node has to have a builder else it is unchanged as it is source to some other target
    # which will have binfo to do a real check if the node needs to be rebuilt
    if not node.is_buildable():
        api.output.verbose_msgf(
            ["node.change"], "{indent}{node} has no builder", node=node.ID, indent=' '*(indent+6))

        return ChangeCheck.SAME

    # we have info so the default is False now
    result = ChangeCheck.SAME

    # the known children to check. This includes sources and explicit depends.
    # the implicit has to be filed in via a scan we we want to delay
    children = (node.sources if node.sources else []) + \
        (node.depends if node.depends else [])

    # now we want to check the children to see if they changed ( if they did we changed as well)
    for child in children:
        # call the child first as we need to go down to the bottom first and then come back up
        result = has_changed(child, indent=indent+1)
        if result & ChangeCheck.DIFF:
            break

    return result


# obsolete checking function


def node_up_to_date(node):
    '''
    Expects a SCons node object, will test against stored info
    to see if it is up to date
    '''

    node = glb.engine.def_env.arg2nodes(node)[0]
    ninfo = node.get_stored_info().ninfo
    return not node.change_timestamp_then_content(node, ninfo)


def abs_path(env, path, create_node):
    path = env.subst(path)
    if path.startswith('#'):
        directory = env.Dir('#')
        path = path[len('#'):]
    else:
        directory = env.Dir(env['SRC_DIR'])
    result = create_node(path, directory)
    return result.srcnode().abspath


def abs_path_node(env, path, create_node):
    path = env.subst(path)
    scons_dir = env.Dir('#')
    directory = env.Dir('$SRC_DIR')
    result = create_node(path, directory)
    if result.is_under(directory):
        # this is under the current parts
        return create_node(directory.rel_path(result))
    elif result.is_under(scons_dir):
        # this is under the SConstruct root
        path = '$OUTOFTREE_BUILD_DIR/' + scons_dir.rel_path(result)
        return create_node(path)
    # it is not under the SConstruct directory
    # we base this off the root directory
    # on windows we need to check for volumes other than C:
    path = result.abspath
    # looks like window path that is not c:\
    if path[1] == ":" and result.abspath[0] != 'C':
        # return path, we cannot map this to a variant directory
        return create_node(result.srcnode().abspath)
    # map to a variant directory
    path = '$ROOT_BUILD_DIR' + path[2:]
    return create_node(path)


# these provide a string Absolute path
class _AbsFile:

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, path):
        return abs_path(self.env, path, self.env.File)


class _AbsDir:

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, path: str):
        return abs_path(self.env, path, self.env.Dir)


def AbsFile(env, path: str):
    return abs_path(env, path, env.File)


def AbsDir(env, path: str):
    return abs_path(env, path, env.Dir)

# these provide a Node that might be tweak to work with
# the Variant Directory of the given Part


class _AbsFileNode:

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, path: str):
        return abs_path_node(self.env, path, self.env.File)


class _AbsDirNode:

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, path):
        return abs_path_node(self.env, path, self.env.Dir)


def AbsFileNode(env, path):
    return abs_path_node(env, path, env.File)


def AbsDirNode(env, path):
    return abs_path_node(env, path, env.Dir)


# add as global to part scope
api.register.add_global_parts_object('AbsFile', _AbsFile, True)
api.register.add_global_parts_object('AbsDir', _AbsDir, True)
api.register.add_global_parts_object('AbsFileNode', _AbsFileNode, True)
api.register.add_global_parts_object('AbsDirNode', _AbsDirNode, True)

# adding logic to Scons Environment object
api.register.add_method(AbsFile)
api.register.add_method(AbsDir)
api.register.add_method(AbsFileNode)
api.register.add_method(AbsDirNode)
