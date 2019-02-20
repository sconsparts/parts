
from __future__ import absolute_import, division, print_function

import copy
import os
import re
import subprocess
import sys

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
        raise Exception("Unsuported OS type: " + sys.platform)

    if shellenv:
        for k, v in shellenv.items():
            if not isinstance(k, str):
                k = k.encode() if glb.isPY2 else k.decode()
            if not isinstance(v, str):
                v = v.encode() if glb.isPY2 else v.decode()
            shellenv[k] = v

    api.output.verbose_msg(["merge_script"], "Calling '{}'".format(cmdLine))
    popen = subprocess.Popen(cmdLine, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=shellenv)

    # Use the .stdout and .stderr attributes directly because the
    # .communicate() method uses the threading module on Windows
    # and won't work under Pythons not built with threading.
    popen.wait()
    stdout = popen.stdout.read()
    if popen.wait() != 0:
        api.output.error_msg(
            "Getting values of environment values of '{}' failed because of return code not equal to 0".format(script))

    output = stdout
    return output.decode()


def parse_output(output, keep=None):

    ret = {}  # this is the data we will return

    # parse everything
    reg = re.compile('(\\w*)=(.*)', re.I)
    for line in output.splitlines():
        m = reg.match(line)
        if m:
            if keep is not None:
                # see if we need to filter out data
                k = m.group(1)
                if k in keep:
                    ret[k] = m.group(2)  # .split(os.pathsep)
            else:
                # take everything
                ret[m.group(1)] = m.group(2)  # .split(os.pathsep)

    # see if we need to filter out data
    if keep is not None:
        pass

    return ret


def get_script_env(env, script, args=None, vars=None):
    '''
    this function returns a dictionary of all the data we want to merge
    or process in some other way.
    '''
    if env['PLATFORM'] == 'win32':
        nenv = normalize_env(env['ENV'], ['COMSPEC'])
    else:
        nenv = normalize_env(env['ENV'], [])

    output = get_output(env.File(script).abspath, args, nenv)
    vars = parse_output(output, vars)
    return vars


def merge_script_vars(env, script, args=None, vars=None):
    '''
    This merges the data retieved from the script in to the Enviroment
    by prepending it.
    script is the name of the script, args is optional arguments to pass
    vars are var we want to retrieve, if None it will retieve everything found
    '''
    shell_env = get_script_env(env, script, args, vars)
    for k, v in shell_env.items():
        env.PrependENVPath(k, v, delete_existing=1)


# adding logic to Scons Enviroment object
SConsEnvironment.MergeScriptVariables = merge_script_vars
SConsEnvironment.GetScriptVariables = get_script_env
