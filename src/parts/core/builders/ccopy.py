# pylint: disable=missing-docstring


import copy
import os
from typing import Dict, List

from builtins import zip

import parts.glb as glb
import parts.api as api
import parts.common as common
import parts.core.util as util
import parts.overrides.symlinks as symlinks
import parts.pattern as pattern
import parts.core.scanners as scanners
from parts.errors import GetPartStackFrameInfo
import SCons.Script
from SCons.Script.SConscript import SConsEnvironment


class CCopyException(Exception):

    def __init__(self, exc):
        Exception.__init__(self)
        self.exc = exc


class CopyBuilderDescription:
    def __init__(self, builderName, ccopyName, copyFunctions):
        self.builderName = builderName
        self.ccopyName = ccopyName
        self.copyFunctions = copyFunctions


def CCopyEmit(target, source, env):
    # target, source = target[0], source[0]
    # target.must_be_same(type(source))
    [copy_metatags(trg, src, env) for trg, src in zip(target, source)]
    # don't delete the target before the copy (speed)
    # target.set_precious(True)
    return target, source


class CCopy:
    default = 0
    copy = 1
    #hard_soft_copy = 2
    #soft_hard_copy = 3
    hard_copy = 4
    #soft_copy = 5

    DEFAULT_NAME = 'hard-copy'

    @classmethod
    def convert(cls, logicName):
        if util.isString(logicName):
            result = getattr(cls, logicName.replace('-', '_'), None)
            if isinstance(result, int):
                return result
            api.output.warning_msgf("unknown string value for CCOPY_LOGIC: {0}", logicName)
        return logicName

    @classmethod
    def getList(cls):
        return [attrName.replace('_', '-') for (attrName, attrValue) in cls.__dict__.items()
                if isinstance(attrValue, int)]

    @classmethod
    def getCopyBuilder(cls, env, copyLogic):
        if copyLogic == cls.default:
            # fallback to the safest copy logic
            copyLogic = cls.convert(env.get('CCOPY_LOGIC', cls.copy))
        else:
            copyLogic = cls.convert(copyLogic)
        try:
            description = COPY_BUILDERS[copyLogic]
        except KeyError:
            description = COPY_BUILDERS[cls.copy]
        return getattr(env, description.builderName)


def copy_metatags(target, source, env):
    '''
    Copy all attribute items from one node to another
    '''
    # this part should be removable with the removal of the hack
    # with symlink and MetaTag()
    try:
        copiedas = source.attributes.copiedas
    except AttributeError:
        source.attributes.copiedas = copiedas = []
    copiedas.append(target)

    # This is needed still
    for k, v in source.attributes.__dict__.items():
        if not k.startswith("_"):
            tmp = copy.copy(v)
            setattr(target.attributes, k, tmp)


def make_batch_value(uid):
    '''
    make a default batch key
    @param uid  This provides a way to separate this key for other keys that would have the 
                same value for the stack we try to get. This is like getting the Part Alias()
                but in many cases this is the env.get_csig() as this is generally faster to get
                and is a unique value independent of the "component" logic in Parts
    '''
    batch_key = GetPartStackFrameInfo()
    # return the part uid-{file of call}-{line in file)
    return uid, hash(batch_key[0]), batch_key[1]

# calls the needed builder based on the type of file, etc


def CCopyAsWrapper(env, target=None, source=None, copy_logic=CCopy.default, **kw):
    # set some values to control the builder action
    _CCOPY_VERBOSE_ = 'False' # todo! map to verbose value is it is set
    _COPY_ONLY_ = 'True' if copy_logic == CCopy.copy else 'False'

    if "CCOPY_BATCH_KEY" not in kw:
        kw['CCOPY_BATCH_KEY'] = make_batch_value(env.get_csig_hash())

    result = []
    source = env.arg2nodes(source)
    target = env.arg2nodes(target)
    api.output.verbose_msg("ccopy", f"CCopyAs called with {len(source)} items")

    if len(target) != len(source):
        api.output.error_msg("Number of targets and sources should be the same")

    for src, tgt in zip(source, target):
        # if the target is a string and the source is a symlink,
        # we want to make the target a symlink as well
        if util.isString(tgt) and isinstance(src, symlinks.FileSymbolicLink):
            targetDirName, targetFileName = os.path.split(tgt)
            tgt = env.Dir(targetDirName).FileSymbolicLink(os.sep.join(('.', targetFileName)))
        
        copyTargets = env._CCopy_(target=tgt, source=src, _COPY_ONLY_=_COPY_ONLY_,
                                  _CCOPY_VERBOSE_=_CCOPY_VERBOSE_, TEMPFILEPREFIX='-@', **kw)
        result.extend(copyTargets)

    return result


def CCopyWrapper(env, target=None, source=None, copy_logic=CCopy.default, **kw):
    if "CCOPY_BATCH_KEY" not in kw:
        kw['CCOPY_BATCH_KEY'] = make_batch_value(env.get_csig_hash())

    # set some values to control the builder action
    _CCOPY_VERBOSE_ = 'True'
    _COPY_ONLY_ = 'True' if copy_logic == CCopy.copy else 'False'

    # convert the target to a node
    target_nodes = env.arg2nodes(target, env.fs.Dir)
    # make sure the source is a list of sources
    sources = common.make_list(source)
    # the finial set of output targets
    result = []

    for node in target_nodes:
        for src in sources:
            if util.isString(src):  # normal builder
                src = env.arg2nodes(src, env.fs.Entry)[0]
                # Prepend './' so the lookup doesn't interpret an initial
                # '#' on the file name portion as meaning the Node should
                # be relative to the top-level SConstruct directory.
                #target_node = node.Entry(os.sep.join(['.', src.name]))
                target_node = node.Entry(src.name)

            elif isinstance(src, pattern.Pattern):  # pattern call CopyAs under the covers
                # get the set of target and sources based on the pattern
                t, sr = src.target_source(node)
                result.extend(env.CCopyAs(target=t, source=sr, **kw))
                continue
            elif isinstance(src, SCons.Node.FS.Dir):  # normal builder
                target_node = node.Dir(src.name)
            elif isinstance(src, symlinks.FileSymbolicLink):
                target_node = node.FileSymbolicLink(src.name)
            elif isinstance(src, (SCons.Node.FS.File,SCons.Node.FS.Entry)):
                #target_node = dnode.File(os.sep.join(['.', src.name]))
                target_node = node.File(src.name)
            else:
                # should not happen...
                target_node = node.Entry(os.sep.join(['.', src.name]))
            
            copyTargets = env._CCopy_(target=target_node, source=src, _COPY_ONLY_=_COPY_ONLY_,
                                      _CCOPY_VERBOSE_=_CCOPY_VERBOSE_, TEMPFILEPREFIX='-@', **kw)
            result.extend(copyTargets)

    return result


def meta_copy(target, source, env):
    for targetEntry, sourceEntry in zip(target, source):
        # Get info if this should be handled as a symlink
        if util.isSymLink(sourceEntry):
            assert sourceEntry.exists() and sourceEntry.linkto
            # A symbolic link can only be a copy of another symlink.
            # Convert a target node to FileSymbolicLink this is needed for
            # correct up-to-date checks during incremental builds
            symlinks.ensure_node_is_symlink(targetEntry, sourceEntry.linkto)
    return 0


ccopy_cmd = '${TEMPFILE("parts-smart-cp --sources $($CHANGED_SOURCES $) --targets $($CHANGED_TARGETS $) --copy-only=$_COPY_ONLY_ --verbose=$($_CCOPY_VERBOSE_ $)")}'


def batch_key(action, env, target, source):
    '''
    For the ccopy builders we expect on source node at a time 
    this function will try to allow scons to batch values together to speed up the builder
    by defining call to the cli, as most of the call here do logic that would be faster than
    the time to create the process.
    '''

    try:
        target[0].attributes._copy_batch_key
        return target[0].attributes._copy_batch_key
    except AttributeError:
        pass
    batch_key = env.get("CCOPY_BATCH_KEY", None)
    batch_key_max = int(env.get("CCOPY_BATCH_KEY_MAX_COUNT", 50))
    # guard from negative numbers
    batch_key_max = 1 if batch_key_max < 1 else batch_key_max
    # our base key
    base_key = (*batch_key,)
    # special logic to deal with symlinks
    source[0].disambiguate()
    symlink = True if util.isSymLink(source[0]) else False
    if symlink:
        symlinks.ensure_node_is_symlink(target[0], source[0].linkto)
        base_key = (*base_key, target[0])
    if env.get('_PARTS_DYN'):
        base_key = ("dyn",*base_key)

    # check grouping to make sure we don't make batch key sets to large
    # if we do SCons will not scale well.
    grp_list = _known_keys.setdefault(base_key, [0])
    grp = len(grp_list)-1  # get number of groups
    cnt = grp_list[grp]  # get the cnt of active group

    # do we need to make a new group
    if cnt > batch_key_max:
        _known_keys[base_key].append(0)
        grp += 1
    # this is what we will return, add to the count
    _known_keys[base_key][grp] += 1
    # full key
    ret_key = (*base_key, grp)
    # set it on node (in case we have two builder with same node.. happen on rebuilds as a pattern or glob can see new nodes as item built before)
    target[0].attributes._copy_batch_key = ret_key
    _known_nodes.add(target[0])
    #print(11,ret_key,target,source)
    return ret_key


ccopy_action = SCons.Action.Action(
    # meta_copy, Comment this out as it looks like we should be ok without it (might be wrong however, but don't have a test case for it)
    ccopy_cmd,
    batch_key=batch_key
)


if not glb.pieces_loaded:
    _known_nodes = set()
    _known_keys: Dict[tuple, List[int]] = {}
    api.register.add_builder(
        '_CCopy_',
        SCons.Builder.Builder(
            action=ccopy_action,
            emitter=CCopyEmit,
            # target_factory=SCons.Node.FS.Dir,
            target_scanner=symlinks.symlink_scanner,
            source_scanner=scanners.NullScanner,
        )
    )

    api.register.add_method(CCopyWrapper, 'CCopy')
    api.register.add_method(CCopyAsWrapper, 'CCopyAs')

    api.register.add_global_object('CCopy', CCopy)
    api.register.add_global_parts_object('CCopy', CCopy)
    api.register.add_enum_variable('CCOPY_LOGIC', CCopy.DEFAULT_NAME, '', CCopy.getList())
