'''
this file provides the AbsFile wrappers. I have not moved this to pieces area
yet as i need a way to safely add the global object to parts export statement
'''
from __future__ import absolute_import, division, print_function

import ctypes
import os

import parts.api as api
import parts.common as common
import parts.core.util as util
import parts.glb as glb
import parts.metatag as metatag
import SCons.Node.FS
import SCons.Script
import SCons.Util
from SCons.Debug import logInstanceCreation
# import the meta object we will need to add our code to as methods
from SCons.Script.SConscript import SConsEnvironment

# this is the decider function map.. need to call decider logic via this map
# of functions

decider_map = SCons.Node._decider_map


class ninfotmp(object):

    def __init__(self):
        if __debug__:
            logInstanceCreation(self)
        self.timestamp = 0
        self.csig = 0


def build_info_changed(self, scan=True, skip_implict=False, indent=0):

    try:
        # if the node was cached with not changed or it is built
        # this mean we can stop and say it is not changed
        if not self.attributes._binfo_changed:
            api.output.verbose_msgf(
            ["binfo-change","node-changed"], "{indent}{node} Cached: False",node=self.ID, indent=" "*indent)
            return False

    except AttributeError:
        pass

    # if the node is build or visited it cannot be viewed as changed anymore
    if self.isBuilt or self.isVisited:
        api.output.verbose_msgf(
            ["binfo-change", "node-changed"],
            "{indent}{node} has been built!", node=self.ID, indent=" "*indent)
        self.attributes._binfo_changed = False
        return False

    # check that the node exists
    # this is where we may want to look at the ninfo..
    # as if it change then the binfo that creates this would
    # be out of sync.. however at the moment SCons does not see this
    if not self.exists():
        api.output.verbose_msgf(
            ["binfo-change", "node-changed"],
            "{indent}{node} does not exist!", node=self.ID, indent=" "*indent)
        self.attributes._binfo_changed = True
        return True

    # the node has to have a builder else it is unchanged as it is source to some other target
    # which will have binfo to do a real check if the node needs to be rebuilt
    if not self.has_builder():
        api.output.verbose_msgf(
            ["binfo-change", "node-changed"],
            "{indent}{node} is not buildable!", node=self.ID, indent=" "*indent)
        self.attributes._binfo_changed = False
        return False

     # then we need to have stored information else this is viewed as changed
    if self.has_stored_info():
        info = self.get_stored_info()
        binfo = info.binfo

        self.children(scan=scan)

        # these are all the children we have in the binfo cache
        if skip_implict:
            # we might have implict already..
            children = self.sources + self.depends
            cached_sigs = binfo.bsourcesigs + binfo.bdependsigs
        else:
            children = self.children(scan=scan)
            cached_sigs = binfo.bsourcesigs + binfo.bdependsigs + binfo.bimplicitsigs

        # check to see if the defined explicts value differ from the the number of nodes that are defined
        # Known bug here is if depend and sources share a node (Fix this. need to provide issue for SCons)
        diff = len(children) - len(cached_sigs)

        if diff:
            api.output.verbose_msgf(
                ["binfo-change", "node-changed", "node-did-change"],
                "{indent}Expicit sources changed for {node} changed!", node=self.ID, indent=" "*indent)
            cached_children = binfo.bsources + binfo.bdepends + binfo.bimplicit
            for c in children:
                if c not in cached_children:
                    api.output.verbose_msgf(
                        ["binfo-change", "node-changed", "node-did-change"],
                        "{indent}{node} was not found in binfo cache", node=c.ID, indent=" "*(indent+1))
            for c in cached_children:
                if c not in children:
                    api.output.verbose_msgf(
                        ["binfo-change", "node-changed", "node-did-change"],
                        "{indent}{node} was in binfo cache but not defined in the node", node=c.ID, indent=" "*(indent+1))
            self.attributes._binfo_changed = True
            return True

        result = False
        for child, prev_ni in zip(children, cached_sigs):
            # do a decider/sig check if the node it out of date
            # if it fails ... it mean the node change because the child use to build this
            # node is different. It does not mean the logic to build the child changed
            if decider_map[self.changed_since_last_build](child, self, prev_ni, self):

                api.output.verbose_msgf(
                    ["binfo-change", "node-changed", "node-did-change"], "{indent}{node} dependent '{child}' changed!", node=self.ID, child=child, indent=" "*indent)
                result = True
                break
    else:
        api.output.verbose_msgf(
            ["binfo-change", "node-changed", "node-did-change"], "{indent}{node} has no stored info: changed!", node=self.ID, indent=" "*indent)
        result = True
    self.attributes._binfo_changed = result
    return result


def node_explict_change(self, binfo=None, indent=0):
    '''
    Check explict state based on what was is defined in the node
    checks that the node change based on cached state. This want to return as fast as it can
    So first change allows us to return result as soon as it is known
    '''
    # if the node is build or visited it cannot be viewed as changed anymore
    if self.isBuilt or self.isVisited:
        return False
    # the node has to have a builder else it is unchanged as it is source to some other target
    # which will have binfo to do a real check if the node needs to be rebuilt
    if not self.has_builder():
        return False

    # then we need to have stored information else this is viewed as changed
    if not binfo:
        if not self.has_stored_info():
            return True
        info = self.get_stored_info()
        binfo = info.binfo

    # the known children to check. This includes sources and explict depends.
    # the implict has to be filed in via a scan we we want to delay
    children = (self.sources if self.sources else []) + \
        (self.depends if self.depends else [])

    cached_sigs = binfo.bsourcesigs + binfo.bdependsigs

    # check to see if the defined explicts value differ from the the number of nodes that are defined
    # Known bug here is if depend and sources share a node (Fix this. need to provide issue for SCons)
    diff = len(children) - len(cached_sigs)
    if diff:
        api.output.verbose_msgf(
            ["node-explict-change", "node-changed"],
            "{indent}Expicit sources changed for {node} changed!", node=self.ID, indent=" "*indent)
        return True

    # this has to be depth first to ensure that dynamic cases are touched correctly
    # however we can cache results to help speed up the checks.
    for child, prev_ni in zip(children, cached_sigs):
        # do a decider/sig check if the node it out of date
        # if it fails ... it mean the node change because the child use to build this
        # node is different. It does not mean the logic to build the child changed
        if decider_map[child.changed_since_last_build](child, self, prev_ni, self):
            api.output.verbose_msgf(
                ["node-explict-change", "node-changed"], "{indent}{node} dependent '{child}' changed!", node=self.ID, child=child, indent=" "*indent)
            return True

    return False


def node_cached_explict_change(self, binfo=None, indent=0):
    '''
    Check explict state based on what was stored in cache
    checks that the node change based on cached state. This want to return as fast as it can
    So first change allows us to return result as soon as it is known
    '''

    # the node has to have a builder else it is unchanged as it is source to some other target
    # which will have binfo to do a real check if the node needs to be rebuilt
    if not self.has_builder():
        return False

    # then we need to have stored information else this is viewed as changed
    if not binfo:
        if not self.has_stored_info():
            return True
        info = self.get_stored_info()
        binfo = info.binfo

    # The cached explict children
    cached_children = binfo.bsources + binfo.bdepends

    cached_sigs = binfo.bsourcesigs + binfo.bdependsigs

    # check to see if the defined explicts value differ from the the number of nodes that are defined
    # Known bug here is if depend and sources share a node (Fix this. need to provide issue for SCons)
    diff = len(cached_children) - len(cached_sigs)
    if diff:
        api.output.verbose_msgf(
            ["node-changed"], "{indent}Expict sources changed for {node} changed!", node=self.ID, indent=" "*indent)
        return True

    # this has to be depth first to ensure that dynamic cases are touched correctly
    # however we can cache results to help speed up the checks.
    for child, prev_ni in zip(cached_children, cached_sigs):
        # do a decider/sig check if the node it out of date
        # if it fails ... it mean the node change because the child use to build this
        # node is different. It does not mean the logic to build the child changed

        if decider_map[child.changed_since_last_build](child, self, prev_ni):
            api.output.verbose_msgf(
                ["node-changed"], "{indent}Dependent changed {node} changed!", node=self.ID, indent=" "*indent)
            return True

    return False


def node_cached_implict_change(self, binfo=None, indent=0):
    '''
    Check implict state based on what was stored in cache
    checks that the node change based on cached state. This want to return as fast as it can
    So first change allows us to return result as soon as it is known
    '''

    # the node has to have a builder else it is unchanged as it is source to some other target
    # which will have binfo to do a real check if the node needs to be rebuilt
    if not self.has_builder():
        return False

    # then we need to have stored information else this is viewed as changed
    if not binfo:
        if not self.has_stored_info():
            return True
        info = self.get_stored_info()
        binfo = info.binfo

    # the known children to check. This includes sources and explict depends.
    # the implict has to be filed in via a scan we we want to delay
    children = binfo.bimplicit
    cached_sigs = binfo.bimplicitsigs

    # this has to be depth first to ensure that dynamic cases are touched correctly
    # however we can cache results to help speed up the checks.
    for child, prev_ni in zip(children, cached_sigs):
        # do a decider/sig check if the node it out of date
        # if it fails ... it mean the node change because the child use to build this
        # node is different. It does not mean the logic to build the child changed

        if decider_map[child.changed_since_last_build](child, self, prev_ni, self):
            api.output.verbose_msgf(
                ["node-changed"], "{indent}Dependent changed {node} changed!", node=self.ID, indent=" "*indent)
            return True

    return False


def node_implict_change(self, scan=True, binfo=None, indent=0):
    '''
    Check the node implict state by doing a scan() on the node
    '''

    # if the node is build or visited it cannot be viewed as changed anymore
    if self.isBuilt or self.isVisited:
        return False

    # the node has to have a builder else it is unchanged as it is source to some other target
    # which will have binfo to do a real check if the node needs to be rebuilt
    if not self.has_builder():
        return False

    # then we need to have stored information else this is viewed as changed
    if not binfo:
        if not self.has_stored_info():
            return True
        info = self.get_stored_info()
        binfo = info.binfo

    if scan:
        self.scan()

    # the known children to check. This includes sources and explict depends.
    # the implict has to be filed in via a scan we we want to delay
    children = self.implicit
    cached_sigs = binfo.bimplicitsigs

    # check to see if the defined explicts value differ from the the number of nodes that are defined
    # Known bug here is if depend and sources share a node (Fix this. need to provide issue for SCons)
    diff = len(children) - len(cached_sigs)
    if diff:
        api.output.verbose_msgf(
            ["node-changed"], "{indent}Implict sources changed for {node} changed!", node=self.ID, indent=" "*indent)
        return True

    # this has to be depth first to ensure that dynamic cases are touched correctly
    # however we can cache results to help speed up the checks.
    for child, prev_ni in zip(children, cached_sigs):
        # do a decider/sig check if the node it out of date
        # if it fails ... it mean the node change because the child use to build this
        # node is different. It does not mean the logic to build the child changed

        if decider_map[child.changed_since_last_build](child, self, prev_ni, self):
            api.output.verbose_msgf(
                ["node-changed"], "{indent}Dependent changed {node} changed!", node=self.ID, indent=" "*indent)
            return True

    return False


def explict_change(node, indent=0):
    '''
    Check the explict children (sources and depends)
    Check is based on defined values via there binfo
    Does not check the implict
    '''

    # if the node is build or visited it cannot be viewed as changed anymore
    if node.isBuilt or node.isVisited:
        return False

    # the node has to have a builder else it is unchanged as it is source to some other target
    # which will have binfo to do a real check if the node needs to be rebuilt
    if not node.is_buildable():
        return False

    # if info is none this is the default result
    result = True
    if node.has_stored_info():
        # then we need to have stored information else this is viewed as changed
        info = node.get_stored_info()
        # we have info so the default is False now
        result = False
        binfo = info.binfo
        # the known children to check. This includes sources and explict depends.
        # the implict has to be filed in via a scan we we want to delay
        children = (node.sources if node.sources else []) + \
            (node.depends if node.depends else [])

        # this has to be depth first to ensure that dynamic cases are touched correctly
        # however we can cache results to help speed up the checks.
        for child in children:
            # call the child first as we need to go down to the bottom first and then come back up
            result = explict_change(child, indent+1)
        if not result:
            # given the children did not change we want to make sure our view of the
            # children did not change
            result = node_explict_change(node, binfo=binfo, indent=indent)

    return result


def cached_explict_change(node, indent=0):
    '''
    Check the explict children (sources and depends)
    Check is based on defined values via there binfo
    Does not check the implict
    '''

    # the node has to have a builder else it is unchanged as it is source to some other target
    # which will have binfo to do a real check if the node needs to be rebuilt
    if not node.is_buildable():
        return False

    # if info is none this is the default result
    result = True
    if node.has_stored_info():
        # then we need to have stored information else this is viewed as changed
        info = node.get_stored_info()
        # we have info so the default is False now
        result = False
        binfo = info.binfo
        # the known children to check. This includes sources and explict depends.
        # the implict has to be filed in via a scan we we want to delay

        children = binfo.bsources + binfo.bdepends

        # this has to be depth first to ensure that dynamic cases are touched correctly
        # however we can cache results to help speed up the checks.
        for child in children:
            # call the child first as we need to go down to the bottom first and then come back up
            result = cached_explict_change(child, indent+1)
        if not result:
            # given the children did not change we want to make sure our view of the
            # children did not change
            result = node_cached_explict_change(node, binfo=binfo, indent=indent)

    return result


def implicit_change(node, scan=False, indent=0):
    '''
    Check the explict children (sources and depends)
    Check is based on defined values via there binfo
    Does not check the implict
    scan controls if this level will use cached implict or not
    The recursive call is alway to scan
    '''
    api.output.verbose_msgf(
        ["implicit-change", "node-changed"], "{indent}Checking {node}", node=node.ID, indent=" "*indent)
    # if the node is build or visited it cannot be viewed as changed anymore
    if node.isBuilt or node.isVisited:
        return False
    # the node has to have a builder else it is unchanged as it is source to some other target
    # which will have binfo to do a real check if the node needs to be rebuilt
    if not node.is_buildable():
        return False

    # in case this is a directory node
    if node.builder is SCons.Node.FS.MkdirBuilder and node.exists():
        return False

    # if info is none this is the default result
    result = True
    if node.has_stored_info():
        # then we need to have stored information else this is viewed as changed
        info = node.get_stored_info()
        # we have info so the default is False now
        result = False
        binfo = info.binfo

        if scan:
            api.output.verbose_msgf(
                ["implicit-change", "node-changed"], "{indent}Scanning {node}", node=node.ID, indent=" "*indent)
            node.scan()
            # the known children to check. This includes sources and explict depends.
            # the implict has to be filed in via a scan we we want to delay
            children = (node.implicit if node.implicit else [])
        else:
            children = binfo.bimplicit
        api.output.verbose_msgf(
            ["implicit-change", "node-changed"], "{indent}implicit {children}", children=common.DelayVariable(lambda: [n.ID for n in children]), indent=" "*indent)
        # this has to be depth first to ensure that dynamic cases are touched correctly
        # however we can cache results to help speed up the checks.
        for child in children:
            # call the child first as we need to go down to the bottom first and then come back up
            result = implicit_change(child, scan=True, indent=indent+1)
        if not result:
            # given the children did not change we want to make sure our view of the
            # children did not change
            if scan:
                # we already scanned.. so don't redo the scan again
                result = node_implict_change(node, scan=False, binfo=binfo, indent=indent)
            else:
                result = node_cached_implict_change(node, binfo=binfo, indent=indent)

    return result


def cached_implicit_change(node, indent=0):
    '''
    Check the explict children (sources and depends)
    Check is based on defined values via there binfo
    Does not check the implict
    scan controls if this level will use cached implict or not
    The recursive call is alway to scan
    '''

    # the node has to have a builder else it is unchanged as it is source to some other target
    # which will have binfo to do a real check if the node needs to be rebuilt
    if not node.is_buildable():
        return False

    # then we need to have stored information else this is viewed as changed
    info = node.get_stored_info()

    # if info is none this is the default result
    result = True
    if info:
        # we have info so the default is False now
        result = False
        binfo = info.binfo

        children = binfo.bimplicit

        # this has to be depth first to ensure that dynamic cases are touched correctly
        # however we can cache results to help speed up the checks.
        for child in children:
            # call the child first as we need to go down to the bottom first and then come back up
            result = cached_implicit_change(child, indent=indent+1)
        if not result:
            # given the children did not change we want to make sure our view of the
            # children did not change
            result = node_cached_explict_change(node, binfo=binfo, indent=indent)

    return result


def has_changed(node, skip_implict=False, indent=0):
    '''
    This function tries to tell if the node changes. This differs from the SCons
    function up_to_date/changed (which are optmized for the task logic) in two ways:
    1) It tries to find if something is different and exits as quick as possible.
        a. only expection at the moment is we do the children size check later.
    2) It check explict depend before calling scanners to get implicit depends

    This should avoid some unneed scans and checks when out of date.
    The logic also does this depth first. this is to ensure better
    environment state in cases of scanner calling builders.

    skip_implict - allows us to skip testing this nodes implict as we maybe testing
    this in the scanner for this node ( so the implicit are not known yet)

    '''

    api.output.verbose_msgf(["node-changed"], "{indent}checking has_changed {node}", node=node.ID, indent=" "*indent)

    # if the node is build or visited it cannot be viewed as changed anymore
    if node.isBuilt or node.isVisited:
        api.output.verbose_msgf(
            ["binfo-change", "node-changed"],
            "{indent}{node} has been built!", node=node.ID, indent=" "*indent)
        node.attributes._changed = False
        return False

    try:
        # if the node was cached with not changed or it is built
        # this mean we can stop and say it is not changed
        if not node.attributes._has_changed:
            api.output.verbose_msgf(
            ["node-changed"], "{indent}{node} Cached: False", node=node.ID, indent=" "*indent)
            return False
        else:
            api.output.verbose_msgf(
            ["node-changed"], "{indent}{node} Cached: True", node=node.ID, indent=" "*indent)
            return True

    except AttributeError:
        pass

    # the node has to have a builder else it is unchanged as it is source to some other target
    # which will have binfo to do a real check if the node needs to be rebuilt
    if not node.is_buildable():
        api.output.verbose_msgf(
            ["node-changed"], "{indent}{node} has no builder", node=node.ID, indent=" "*indent)
        node.attributes._changed = False
        return False

    # if info is none this is the default result
    result = True
    if node.has_stored_info():
        # we have info so the default is False now
        result = False

        ###################################################
        # we have to scan at this point to make sure all environmental additions
        # at added. It would be nice if we have a way to add a node that had to be
        # processed first like a prerequisites that did not effect the depends or action
        # and would be stored in the cache so we new to process these first to make sure
        # the incremental build would be correctly. This would allow us to delay scanning
        # until it was needed for an updated check.
        children = node.children(scan=True)

        # now we want to check the children to see if they changed ( if they did we changed as well)
        for child in children:
            # call the child first as we need to go down to the bottom first and then come back up
            result = has_changed(child, indent=indent+1)
            if result:
                api.output.verbose_msgf(
                ["node-changed", "node-did-change"], "{indent}{node} changed!.", node=node.ID, indent=" "*indent)
                break

        if not result:
            # given the children did not change we want to make sure our view of the
            # children did not change
            # don't need to scan again
            result = build_info_changed(node, scan=False, skip_implict=skip_implict, indent=indent+1)
            #node_explict_change(node, binfo=binfo, indent=indent)
            if result:
                api.output.verbose_msgf(["node-changed", "node-did-change"],
                                        "{indent}{node} changed!.", node=node.ID, indent=" "*indent)
            else:
                api.output.verbose_msgf(["node-changed"], "{indent}{node} did not change.", node=node.ID, indent=" "*indent)

    else:
        api.output.verbose_msgf(
            ["node-changed", "node-did-change"], "{indent}{node} has no stored info: changed!", node=node.ID, indent=" "*indent)
    node.attributes._has_changed = result
    return result


def has_children_changed(node, indent=0):
    '''
    Like has_changed expect that we only care if the depends and sources need to be updated
    given that this node probally needs to be updated still
    '''

    api.output.verbose_msgf(["node-changed"], "{indent}checking children {node}", node=node.ID, indent=" "*indent)

    # the node has to have a builder else it is unchanged as it is source to some other target
    # which will have binfo to do a real check if the node needs to be rebuilt
    if not node.is_buildable():
        api.output.verbose_msgf(
            ["node-changed"], "{indent}{node} has no builder", node=node.ID, indent=" "*indent)

        return False

    # we have info so the default is False now
    result = False

    # the known children to check. This includes sources and explict depends.
    # the implict has to be filed in via a scan we we want to delay
    children = (node.sources if node.sources else []) + \
        (node.depends if node.depends else [])

    # now we want to check the children to see if they changed ( if they did we changed as well)
    for child in children:
        # call the child first as we need to go down to the bottom first and then come back up
        result = has_changed(child, indent=indent+1)
        if result:
            break

    return result


# obsolete checking function


def node_up_to_date(node):
    '''
    Expects a SCons node object, will test against stored info
    to see if it is uptodate
    '''

    node = glb.engine.def_env.arg2nodes(node)[0]
    ninfo = node.get_stored_info().ninfo
    return not node.changed_timestamp_then_content(node, ninfo)


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
    # it is not under the Sconstruct directory
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
class _AbsFile(object):

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, path):
        return abs_path(self.env, path, self.env.File)


class _AbsDir(object):

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, path):
        return abs_path(self.env, path, self.env.Dir)


def AbsFile(env, path):
    return abs_path(env, path, env.File)


def AbsDir(env, path):
    return abs_path(env, path, env.Dir)

# these provide a Node that might be tweak to work with
# the Variant Directory of the given Part


class _AbsFileNode(object):

    def __init__(self, env):
        if __debug__:
            logInstanceCreation(self)
        self.env = env

    def __call__(self, path):
        return abs_path_node(self.env, path, self.env.File)


class _AbsDirNode(object):

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

# adding logic to Scons Enviroment object
SConsEnvironment.AbsFile = AbsFile
SConsEnvironment.AbsDir = AbsDir
SConsEnvironment.AbsFileNode = AbsFileNode
SConsEnvironment.AbsDirNode = AbsDirNode
