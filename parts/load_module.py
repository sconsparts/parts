
import sys
import os
import imp
import traceback
import re

import SCons.Errors
import SCons.Script

import glb
import api.output


g_site_dir_cache = {}


def get_site_directories(subdir):
    try:
        return g_site_dir_cache[subdir]
    except KeyError:
        if glb._host_sys is None:
            print "host_os bootstrap bug"
            1 / 0

        host_os = glb._host_sys  # can't use HOST_OS because of bootstrap issue.
        localpath = []
        # local data
        localpath = [
            # homedir/.parts-site
            os.path.join(os.path.expanduser('~'), 'parts-site', subdir),
            os.path.join(os.path.expanduser('~'), '.parts-site', subdir)
        ]
        # add paths for windows
        if host_os == 'win32':
            # if we run as a service (like running in buildbot) we may not have a user directory
            if os.environ.has_key('APPDATA'):
                localpath.append(os.path.join(os.environ['APPDATA'], 'parts-site', subdir))
            # global system area. should not be needed.. just being careful
            if os.environ.has_key('ALLUSERSPROFILE'):
                syspath = [os.path.join(os.environ['ALLUSERSPROFILE'], 'parts-site', subdir)]
            else:
                syspath = []
        elif host_os == 'darwin':
            syspath = [os.path.join('/Library/Application Support/parts', 'parts-site', subdir)]
        else:
            # some kind of POSIX, most likely Linux
            syspath = [os.path.join('/usr/share/parts', 'parts-site', subdir)]

        if SCons.Script.GetOption('use_part_site'):
            sitepaths = [
                os.path.join(os.path.abspath(SCons.Script.GetOption('use_part_site')), subdir),
                # parts install
                os.path.join(glb.parts_path, subdir)
            ]
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
            ] + localpath + syspath + [
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
    modname = '<%s>%s' % (type, name)
    try:
        return sys.modules[modname]
    except KeyError:
        api.output.verbose_msg('load_module',
                               'Trying to load module <%s> type <%s>' % (name, type))
        file, path1, desc = imp.find_module(name, pathlst)
        oldPath = sys.path[:]
        sys.path = pathlst + sys.path
        try:
            mod = imp.load_module(modname, file, path1, desc)
            api.output.verbose_msg("load_module", "Module was loaded from <%s>" % path1)
        except ImportError:
            api.output.verbose_msg("load_module", "Failed to load module!")
            api.output.verbose_msg(["load_module_failure", "load_module"],
                                   "Stack:\n%s" % traceback.format_exc())
            raise SCons.Errors.UserError, "No module named '%s'" % (name)
        finally:
            sys.path = oldPath
            if file:
                file.close()

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
                files = os.walk(path).next()[2]
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
