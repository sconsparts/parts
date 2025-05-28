

import importlib.machinery
import importlib.util

import os
import re
import sys
import traceback

import parts.api as api
import parts.glb as glb
import SCons.Script

g_site_dir_cache = {}


def get_site_directories(subdir):
    try:
        return g_site_dir_cache[subdir]
    except KeyError:
        if glb._host_platform is None:
            print("host_os bootstrap bug")
            1 / 0

        host_os = glb._host_platform  # can't use HOST_OS because of bootstrap issue.
        # local data
        localpaths = [
            # homedir/.parts-site
            os.path.join(os.path.expanduser('~'), 'parts-site', subdir),
            os.path.join(os.path.expanduser('~'), '.parts-site', subdir)
        ]
        # add paths for windows
        if host_os == 'win32':
            # if we run as a service (like running in buildbot) we may not have a user directory
            if 'APPDATA' in os.environ:
                localpaths.append(os.path.join(os.environ['APPDATA'], 'parts-site', subdir))
            # global system area. should not be needed.. just being careful
            if 'ALLUSERSPROFILE' in os.environ:
                syspaths = [os.path.join(os.environ['ALLUSERSPROFILE'], 'parts-site', subdir)]
        elif host_os == 'darwin':
            # by convention on macOS, app data goes into
            # /Library/Application Support or ~/Library/Application Support
            # but many UNIX-style tools still use /usr/local/share.
            # /usr/share is typically hard read-only
            syspaths = [
                os.path.join('/Library/Application Support/parts', 'parts-site', subdir),
                os.path.join('/usr/local/share/parts', 'parts-site', subdir)
            ]
            localpaths.append(os.path.join(os.path.expanduser('~/Library/Application Support/parts'), 'parts-site', subdir))
        else:
            # some kind of POSIX, most likely Linux
            syspaths = [
                os.path.join('/usr/share/parts', 'parts-site', subdir),
                os.path.join('/usr/local/share/parts', 'parts-site', subdir)
            ]

        if SCons.Script.GetOption('use_part_site'):
            sitepaths = [
                os.path.join(os.path.abspath(SCons.Script.GetOption('use_part_site')), subdir),
                # parts install
                os.path.join(glb.parts_path, subdir)
            ]
        # if true don't add global location
        elif SCons.Script.GetOption('global_part_site'):
            sitepaths = [
                # current directory parts_site or user pointed site
                os.path.join(glb.sconstruct_path, 'parts-site', subdir),
                os.path.join(glb.sconstruct_path, '.parts-site', subdir),
                # user part-site in parts install
                os.path.join(glb.parts_path, 'parts-site', subdir),
                # parts install
                os.path.join(glb.parts_path, subdir)
            ]
        else:
            sitepaths = [
                # current directory parts_site or user pointed site
                os.path.join(glb.sconstruct_path, 'parts-site', subdir),
                os.path.join(glb.sconstruct_path, '.parts-site', subdir)
                # homedir/.parts-site
            ] + localpaths + syspaths + [
                # user part-site in parts install
                os.path.join(glb.parts_path, 'parts-site', subdir),
                # parts install
                os.path.join(glb.parts_path, subdir)
            ]

        g_site_dir_cache[subdir] = sitepaths
    return g_site_dir_cache[subdir]


def load_module(pathlst, name, type):
    """Return the imported module
    made more generic so Parts can reuse the logic
    instead of using the C&P anti-patttern.
    """
    # modname = '<{type}>{name}'.format(type=type, name=name)
    modname = f'parts.{type}.{name}'
    #modname = name

    if modname in sys.modules:
        return sys.modules[modname]
    spec = importlib.machinery.PathFinder.find_spec(name, pathlst)
    if spec is not None:
        #print(f"spec.name={spec.name}, modname={modname}")
        #spec.name = modname
        #print(f"here {spec}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[modname] = mod

        #print(f"Loaded mod = {mod}")
        spec.loader.exec_module(mod)
        #api.output.verbose_msg("load_module", "Module was loaded from {path}".format(path=path1))
    else:
        api.output.verbose_msg("load_module", f"Failed to load module {modname}!\n Not found on Path: {pathlst}")
        return
        #api.output.verbose_msg("load_module", "Failed to load module!")
        #api.output.verbose_msg(["load_module_failure", "load_module"], "Stack:\n{0}".format(traceback.format_exc()))
        #raise SCons.Errors.UserError("Module named '{name}' failed to load!".format(name=name))


    return sys.modules[modname]


# replace this with cache for Pattern object as well
# with will address issue with file scan speed
g_glob_cache = {}
PYMODULE_RE = re.compile(r'^(.*?)\.py.?', re.IGNORECASE)


def get_possible_modules(pathList):
    result = set()
    for path in pathList:
        try:
            modules = g_glob_cache[path]
        except KeyError:
            modules = set()
            try:
                files = next(os.walk(path))[2]
            except StopIteration:
                # path does not exist so it does not contain any modules
                pass
            else:
                for fn in files:
                    try:
                        modules.add(PYMODULE_RE.match(fn).group(1))
                    except AttributeError:
                        # this file doesn't match our Python module pattern
                        pass
            g_glob_cache[path] = modules
        result |= modules
    return result


def get_path_with_modules(paths):
    ret = {}
    for path in paths:
        tmp = get_possible_modules([path])
        if tmp:
            ret[path] = get_possible_modules([path])
    return ret
