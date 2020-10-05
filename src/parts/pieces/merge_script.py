

import copy
import os
import re
import subprocess
import sys
import pprint

import parts.api as api
import parts.glb as glb
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment


def normalize_env(shellenv=None, keys=None):
    """Given a dictionary representing a shell environment, add the variables
    from os.environ needed for the processing of .bat files; the keys are
    controlled by the keys argument.

    It also makes sure the environment values are correctly encoded.

    Note: the environment is copied"""
    normenv = {}
    # copy the shell env
    if shellenv:
        normenv.update(shellenv)

    # copy over any key from shell environment
    if keys:
        for k in keys:
            if k in os.environ:
                normenv[k] = os.environ[k]

    # on windows we need to convert unicode text to mbcs
    # because of odd bug with subprocess
    if sys.platform == 'win32':
        for k in list(normenv.keys()):
            normenv[k] = copy.deepcopy(normenv[k]).encode('mbcs')

    return normenv


def get_output(script, args=None, shellenv=None):
    """Parse the output of given bat file, with given args."""
    if sys.platform == 'win32':
        cmdLine = '"%s" %s & set' % (script, (args if args else ''))
        shell = False
    elif sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        cmdLine = '. {script} {args} ; set'.format(script=script, args=args if args else '')
        shell = True
    else:
        raise Exception("Unsupported OS type: " + sys.platform)

    if shellenv:
        for k, v in shellenv.items():
            if not isinstance(k, str):
                k = k.encode() if glb.isPY2 else k.decode()
            if not isinstance(v, str):
                v = v.encode() if glb.isPY2 else v.decode()
            shellenv[k] = v

    api.output.verbose_msg(["merge_script"], "Calling '{}'".format(cmdLine))
    popen = subprocess.run(cmdLine, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=shellenv)
    
    if popen.returncode != 0:
        api.output.error_msg(
            "Getting values of environment values of '{}' failed because of return code not equal to 0".format(script))

    # Use the .stdout and .stderr attributes directly because the
    # .communicate() method uses the threading module on Windows
    # and won't work under Pythons not built with threading.
    output = popen.stdout

    return output.decode()


def parse_output(output, keep=None, remove=None, nenv={}):

    ret = {}  # this is the data we will return
    # these are the default items we want to remove
    filter_keys = ("LS_COLORS", "BASHOPTS", "SHELLOPTS", "PPID", "POSIXLY_CORRECT")
    if remove:
        filter_keys = filter_keys + tuple(remove)

    # parse everything
    reg = re.compile('(\\w*)=(.*)', re.I)
    for line in output.splitlines():
        m = reg.match(line)
        if m:
            key = m.group(1)
            if keep:
                # see if we need to filter out data
                for regk in keep:
                    if re.match(regk, key):
                        ret[key] = m.group(2)
                        break
            else:
                # take everything that should not be skipped
                skip = False
                for regk in filter_keys:
                    if re.match(regk, key):
                        skip = True
                        break
                if not skip and key == "PATH":
                    # we want to remove the base default items in the path else later merging can have some odd effects
                    new_paths = m.group(2).split(os.pathsep)
                    org_path = nenv.get("PATH", "").split(os.pathsep)
                    ret[key] = os.pathsep.join([path for path in new_paths if path.lower() not in org_path])

                elif not skip:
                    ret[key] = m.group(2)

    api.output.verbose_msg(["merge_script"], "Environment '{}'".format(pprint.pformat(ret)))

    return ret


def get_script_env(env, script, args=None, vars=None, remove=None):
    '''
    this function returns a dictionary of all the data we want to merge
    or process in some other way.
    '''
    if env['PLATFORM'] == 'win32':
        nenv = normalize_env(env['ENV'], ['COMSPEC'])
    else:
        nenv = normalize_env(env['ENV'], [])

    output = get_output(env.File(script).abspath, args, nenv)
    vars = parse_output(output, vars, remove, nenv)
    return vars


def merge_script_vars(env, script, args=None, vars=None, remove=None):
    '''
    This merges the data retrieved from the script in to the Environment
    by prepending it.
    script is the name of the script, args is optional arguments to pass
    vars are var we want to retrieve, if None it will retrieve everything found
    '''
    shell_env = get_script_env(env, script, args, vars, remove)
    for k, v in shell_env.items():
        env.PrependENVPath(k, v, delete_existing=1)


# adding logic to Scons Environment object
SConsEnvironment.MergeScriptVariables = merge_script_vars
SConsEnvironment.GetScriptVariables = get_script_env
