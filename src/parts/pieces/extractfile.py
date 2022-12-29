from typing import Dict, List, cast, Union, Generic
from xml.etree.ElementInclude import include
import zipfile
import tarfile
from pathlib import Path
import sys
import os
import json
import hashlib

from parts.common import make_list, matches, extend_unique, TypeVar
import parts.api as api
import parts.glb as glb
import parts.core.scanners as scanners


import SCons.Action
from SCons.Script.SConscript import SConsEnvironment

g_cache: Dict[str, Union[List[zipfile.ZipInfo], List[tarfile.TarInfo]]] = {}

T = TypeVar("T")


def filter_nodes(env, filtergrps, enities: Union[List[zipfile.ZipInfo], List[tarfile.TarInfo]]) -> Union[List[zipfile.ZipInfo], List[tarfile.TarInfo]]:
    # def filter_nodes(env, filtergrps, enities: List[T]) -> List[T]:
    '''
    We filter based on two value nodes that are passed in
    explict_includes if True means if we have to add "*" in includes we can ignore the excludes
    this is used for the case of the json builder that defines what we have to extract. Given the json builder
    can be called multi times it is possible that on of the calls would want to extract all the files, negating the exclude logic
    This has a side effect to prefer what is in includes vs the excludes
    '''

    ret: List[T] = []
    if not filtergrps or filter_nodes == ['==']:
        return enities
    for grp in filtergrps:
        tmp = grp.split("==")
        include = ["*"] if tmp[0] in ('', '*') else tmp[0].split(',')
        exclude = tmp[1].split(',') if tmp[1] else []
        # just exit when we have a * with no exclude
        if include == ['*'] and not exclude:
            return enities

        extend_unique(ret, [node for node in enities if matches(
            node.filename if isinstance(node, zipfile.ZipInfo) else node.name, include, exclude)])

    return ret


def get_nodes_tar(source, env) -> List[tarfile.TarInfo]:
    # get all the nodes, given we have not read this in file yet
    src = source[0].srcnode().abspath
    filternodes = [n.ID[4:] for n in source if n.ID.startswith("grp:")]
    if src in g_cache:
        info = g_cache[src]
    else:
        with tarfile.open(src) as zfile:
            info = [tmp for tmp in zfile.getmembers() if not tmp.isdir()]
        g_cache[src] = info

    # filter the node is we have any patterns
    info = cast(List[tarfile.TarInfo], filter_nodes(env, filternodes, info))
    return info


def get_nodes_zip(source, env) -> List[zipfile.ZipInfo]:
    # get all the nodes
    # Check the in mem cache
    src = source[0].srcnode().abspath
    filternodes = [n.ID[4:] for n in source if n.ID.startswith("grp:")]
    if src in g_cache:
        info = g_cache[src]
    else:
        with zipfile.ZipFile(src) as zfile:
            info = [tmp for tmp in zfile.infolist() if not tmp.is_dir()]
        g_cache[src] = info

    # filter the node is we have any patterns
    info = cast(List[zipfile.ZipInfo], filter_nodes(env, filternodes, info))
    return info


def emit_unzip(target, source, env):
    if env.get("return_nodes"):
        target = get_nodes_zip(target, source, env)
    return target, source

 # todo! add symlink logic


def emit_tar(target, source, env):
    if env.get("return_nodes"):
        target = get_nodes_tar(target, source, env)
    return target, source


def emit_extact(target, source, env):
    env.Clean(target[0], target)
    return target, source


extract_action = SCons.Action.Action(
    f"{sys.executable} {os.path.join(glb.parts_path,'scripts','extract.py')} --out-directory $TARGET --json-data $SOURCES",
    cmdstr=f"python3 {os.path.join(glb.parts_path,'scripts','extract.py')} --out-directory $TARGET --json-data $SOURCES",
)


def emit_info(target, source, env):
    #print(source[0], source[0].exists())
    # define a state file to pass the CLI builder with all the state it needs
    # we define a hash to help with the json file having a unqiue name
    target_hash = hashlib.md5()
    # normalize the value
    target_hash.update(Path(source[1].ID).name.encode())
    target = [
        env.File(f"$PARTS_SYS_DIR/${{PART_ALIAS}}extractfile-{Path(target[0].name).name}{source[1].name}{target_hash.hexdigest()}.jsn")]
    return target, source


def get_nodes(target, source, env):
    if source[0].ID.endswith(".zip"):
        nodes = get_nodes_zip(source, env)
    else:
        nodes = get_nodes_tar(source, env)
    return [target.File(node.filename)[0] for node in nodes]


def build_info(target, source, env):
    if source[0].ID.endswith(".zip"):
        node = get_nodes_zip(source, env)
        data = {}
        for item in node:
            item: zipfile.ZipInfo
            data[item.filename] = dict(
                size=item.file_size
            )
    else:
        node = get_nodes_tar(source, env)
        data = {}
        for item in node:
            item: tarfile.TarInfo
            data[item.name] = dict(
                size=item.size
            )
    # store information
    data = {
        'source': source[0].path,
        'files': data
    }

    with open(target[0].ID, mode="w") as outfile:
        json.dump(data, outfile)

    return 0


def extract_files(env, target, source, includes: Union[str, List[str]] = None, excludes: Union[str, List[str]] = None, return_nodes: bool = False):
    # extract file data into a json file.
    # for this to be a "multi" type buider for the json file, we need to pass in the different possible
    # include or exclude patterns as a value node
    include = ",".join(make_list(includes)) if includes else ""
    exclude = ",".join(make_list(excludes)) if excludes else ""
    pattern = [env.Value(f"grp:{include}=={exclude}")]
    # We need to use the target directory as part of the value for the json file we will generate
    # however we cannot have it viewed as a directory yet in SCons as it will break the node chain logic
    # so we pass it as a Value node.
    info = env._ExtractInfo([source]+[env.Value(target)]+pattern)
    # use the info to define what we will extract
    dir_target = env._ExtractFiles(target, info)
    if return_nodes == True or (return_nodes == "auto" and (include or exclude)):
        out_nodes = get_nodes(dir_target, env.arg2nodes(source, env.fs.File)+pattern, env)
        if len(out_nodes) > 30000:
            api.output.warning_msg(
                f"Large number of node being processed for {source}.\n This may take a while.\n To speed up set argument `return_nodes=False`",
                env=env)
        env.SideEffect(out_nodes, dir_target)
        return out_nodes
    return dir_target


api.register.add_method(extract_files, 'ExtractFiles')

build_info_action = SCons.Action.Action(build_info, cmdstr="Extacting information about items to extract from ${SOURCES[0]}")

api.register.add_builder(
    '_ExtractInfo',
    SCons.Builder.Builder(
        action=build_info_action,
        emitter=emit_info,
        target_factory=SCons.Node.FS.File,
        source_scanner=scanners.NullScanner,
        target_scanner=scanners.NullScanner,
        multi=True,
    )
)

api.register.add_builder(
    '_ExtractFiles',
    SCons.Builder.Builder(
        action=extract_action,
        emitter=emit_extact,
        target_factory=SCons.Node.FS.Dir,
        source_scanner=scanners.NullScanner,
        target_scanner=scanners.NullScanner,
    )
)
