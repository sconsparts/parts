from __future__ import absolute_import, division, print_function

from builtins import zip

import os
import re
import sys

import parts.api as api
import parts.api.output as output

import SCons.Builder
import SCons.Script
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment


def addXmlHeader(target, source, env):
    XmlHeader = env.subst('$XML_HEADER')
    for outfile, infile in zip(target, source):
        with open(infile.abspath, 'r') as inputf:
            lines = inputf.read().splitlines(True)
        lines[1:1] = [XmlHeader + '\n']
        with open(outfile.abspath, 'w') as outputf:
            outputf.write(''.join(lines))
    return 0


def addXmlHeader_emitter(target, source, env):
    output = []
    if len(target) != 1:
        api.output.error_msg("Only one input is allowed")

    try:
        dnode = env.arg2nodes(target, env.fs.Dir)[0]
    except TypeError:
        api.output.error_msg(
            "Target `%s' is a file, but should be a directory.  Perhaps you have the arguments backwards?" % str(dir))

    for s in source:
        output.append(env.File(s.name, dnode))
    return (output, source)


api.register.add_builder('__AddXmlHeader__', SCons.Script.Builder(
    action=SCons.Script.Action(addXmlHeader, varlist=['XML_HEADER']),
    emitter=addXmlHeader_emitter,
    target_factory=SCons.Node.FS.Entry
))


def AddXmlHeader(env, target, source, sub_dir='.', **kw):
    if sub_dir is not '.':
        tmp_target = os.path.join(target, sub_dir)
    else:
        tmp_target = target
    return env.__AddXmlHeader__(tmp_target, source, **kw)


def AddXmlHeaderAs(env, target, source, **kw):
    output = []
    for target_i, source_i in zip(target, source):
        target_path = os.path.split(str(target_i))[0]
        output += AddXmlHeader(env, target_path, source_i)
    return output



# adding logic to Scons Enviroment object
SConsEnvironment.AddXmlHeader = AddXmlHeader
SConsEnvironment.AddXmlHeaderAs = AddXmlHeaderAs
