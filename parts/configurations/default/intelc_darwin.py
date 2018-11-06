######################################
# Intel compiler configurations default-darwin
######################################
from __future__ import absolute_import, division, print_function

from past.builtins import basestring
import os

from parts.config import *


def make_bool(obj):
    if isinstance(obj, basestring):
        return obj.lower() in ('true', '1')
    return obj


def map_default_version(env):
    return env['INTELC_VERSION']


def post_process_func(env):
    try:
        env['GCC'].VERSION
    except (AttributeError, KeyError):
        raise RuntimeError("You need to define gnutools or compatible tool chain with Intel tool chain")

    env.AppendUnique(CCFLAGS=['-gcc-name=${GCC.TOOL}', '-gxx-name=${GXX.TOOL}'] + (
        # -gcc-version is deprecated in 13.1, use it only for older compilers
        env['INTELC_VERSION'] < '13.1' and ['-gcc-version=${"".join(str(GCC.VERSION).split("."))}'] or []))

    # code coverage feature additions
    if make_bool(env.get('codecov', False)):
        if(env.Version(env['INTELC_VERSION']) >= 11):
            env.AppendUnique(CCFLAGS=['-prof-gen=srcpos'])
        else:
            env.AppendUnique(CCFLAGS=['-prof-genx'])


config = configuration(map_default_version, post_process_func)
