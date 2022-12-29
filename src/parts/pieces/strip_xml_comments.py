

import os
import re
from builtins import zip

import parts.api as api
import SCons.Script
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

xmlComment = re.compile(r'(.*)(<!--)(.*)(-->)(.*)')

commentStart = re.compile(r'(<!--)')
commentEnd = re.compile(r'(-->)')
keepCommentIfString = '<!--@NOSTRIP'
commentStartString = '<!--'


def scanFile(env, infile, outfile):
    incompleteLine = ""
    with open(outfile.abspath, 'w') as outputf:
        with open(infile.abspath) as inputf:
            for line in inputf.read().splitlines(True):
                line = line.rstrip()

                # if "<!--", i.e. comment start and not  "-->",
                # i.e. comment end save line and read next line
                if incompleteLine:
                    if commentEnd.search(line):
                        line = incompleteLine + line
                        incompleteLine = ""
                    else:
                        incompleteLine += line
                        continue
                elif commentStart.search(line) and not commentEnd.search(line):
                    incompleteLine = line
                    continue

                line_o = stripRecursive(env, line).rstrip()
                if line_o != "":
                    outputf.writelines(line_o + '\n')

# strip multiple comment lines


def stripRecursive(env, line):
    match = xmlComment.match(line)
    if match:
        comment = match.group(1)
        if re.search('<!--', comment):  # careful, multiple comments

            # remove nested comment(s) for now
            newLine = stripRecursive(env, match.group(1)) + match.group(match.lastindex)
            line = line.replace(line, newLine)
            return line
        else:
            if re.search(keepCommentIfString, line) > 0:
                # remove "comment keep string" and keep the comment
                line = line.replace(keepCommentIfString, commentStartString)
            else:
                newLine = match.group(1) + match.group(match.lastindex)
                line = line.replace(line, newLine)
            return line
    else:
        return line


def stripXmlComments(target, source, env):
    for i, tfile in enumerate(target):
        scanFile(env, source[i], tfile)
    return 0


def stripXmlComments_emitter(target, source, env):
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


api.register.add_builder('__StripXMLComments__', SCons.Script.Builder(
    action=SCons.Script.Action(stripXmlComments),
    emitter=stripXmlComments_emitter,
    target_factory=SCons.Node.FS.Entry
))


def StripXMLComments(env, target, source, sub_dir='.', **kw):
    if sub_dir != '.':
        tmp_target = os.path.join(target, sub_dir)
    else:
        tmp_target = target

    return env.__StripXMLComments__(tmp_target, source, **kw)


def StripXMLCommentsAs(env, target, source, **kw):

    output = []
    for target_i, source_i in zip(target, source):
        target_path = os.path.split(str(target_i))[0]
        output += StripXMLComments(env, target_path, source_i, **kw)
    return output


# adding logic to Scons Environment object
api.register.add_method(StripXMLComments)
api.register.add_method(StripXMLCommentsAs)

# vim: set et ts=4 sw=4 ai :
