# this builder is for taking a file and encoding it in a different format
# this is useful for certain i18n cases when you might have a file in a certain
# encoding and you want to translate it to a different code page that might
# be used on a users system


import codecs
from builtins import map, zip

import parts.api as api
import parts.common as common
import SCons.Action
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment


def _encode_bd(target, source, env):
    src_encode = env['ENCODE_SOURCE']
    target_encode = env['ENCODE_TARGET']
    # Foreach target we match it to a single source
    for t, s in zip(target, source):
        # open source
        with codecs.open(str(s), "r", src_encode) as sf:
            content = sf.read()
        with codecs.open(str(t), "w", target_encode) as tf:
            tf.write(content)

    return None


def _encode_sf(target, source, env):
    return "Encoding %s from %s to %s in file %s" % (
        source, env['ENCODE_SOURCE'][0], env['ENCODE_TARGET'][0], target)


def _EncodeFile(env, target, source, target_encoding, source_encoding='utf-8'):
    target = common.make_list(target)
    source = common.make_list(source)
    assert len(target) == len(source), \
        ("Installing source %s into target %s: "
         "target and source lists must have same length.") % (
            list(map(str, source)), list(map(str, target)))
    return env.__EncodeFile(target=target,
                            source=source,
                            ENCODE_SOURCE=source_encoding,
                            ENCODE_TARGET=target_encoding
                            )


# adding logic to Scons Environment object
api.register.add_method(_EncodeFile, 'EncodeFile')


encodeAction = SCons.Action.Action(_encode_bd, _encode_sf,
                                   varlist=['ENCODE_SOURCE', 'ENCODE_TARGET'])
api.register.add_builder('__EncodeFile', SCons.Builder.Builder(action=encodeAction,
                                                               source_factory=SCons.Node.FS.File,
                                                               target_factory=SCons.Node.FS.File))
