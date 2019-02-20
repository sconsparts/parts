# general tool for signing a file
# default to the moment signtool on windows...
# all other places need to be filled in

from __future__ import absolute_import, division, print_function

import os

import parts.api.output as output
import parts.common as common
import parts.tools.Common
import SCons.Action
import SCons.Defaults
import SCons.Errors
import SCons.Platform.win32
import SCons.Script
import SCons.Tool
import SCons.Util
from parts.tools.MSCommon import msvc, validate_vars


def signEmit(target, source, env):
    t = []
    src_dir = env.Dir("$SRC_DIR").abspath
    build_dir = env.Dir("$BUILD_DIR").abspath
    if len(target) == len(source) and len(source) == 1:
        t = [env.Dir("signed").File(env.Dir(build_dir).rel_path(source[0]))]
    elif len(target) == len(source):
        t = target
    else:
        for c, s in enumerate(source):
            if s.abspath.startswith(build_dir):
                s = env.Dir("signed").File(env.Dir(build_dir).rel_path(s))
            elif s.abspath.startswith(src_dir):
                s = env.Dir("signed").File(env.Dir(build_dir).rel_path(s))
            t.append(s)
    return (t, source)


def CertFunc(env):
    if float(env['MSVC_VERSION']) < 7.1:
        return 0

    if not env['SIGNING'].GENCERT:
        return 0

    ret = certAction([], [], env)
    if ret:
        raise SCons.Errors.UserError("Unable to make code signing certificate")

    print("Successfully generated code signing certificate")

    return ret


def SignFunc(target, source, env):
    if float(env['MSVC_VERSION']) < 7.1:
        return 0

    if not env['SIGNING'].ENABLED:
        return 0

    signed = str(target[0]) + '.signed'
    compositeSign = signAction + SCons.Defaults.Touch(signed)
    ret = compositeSign(target[:1], [], env)
    env.File(signed)
    env.Depends(signed, target)
    if ret:
        if env['SIGNING'].GENCERT:
            # try making cert and signing again
            ret = CertFunc(env)
            if ret:
                return ret
            ret = compositeSign(target[:1], [], env)

        if ret:
            raise SCons.Errors.UserError("Unable to sign %s" % target[0])

    print("Successfully signed %s" % target[0])

    return ret


# General signing actions
certAction = SCons.Action.Action("$MAKECERTCOM", "$MAKECERTCOMSTR")
certCheck = SCons.Action.Action(CertFunc, None)

signAction = SCons.Action.Action("$SIGNCOM", "$SIGNCOMSTR")
signCheck = SCons.Action.Action(SignFunc, None)


def generate(env):
    env.SetDefault(MAKECERT='makecert')
    env.SetDefault(MAKECERTFLAGS='-sk "$SIGNING.STORAGE.PRIVATE" -ss "$SIGNING.STORAGE.PUBLIC" -n "$SIGNING.NAME"')
    env.SetDefault(MAKECERTCOM='$MAKECERT $MAKECERTFLAGS')

    env.SetDefault(SIGNTOOL=parts.tools.Common.toolvar('signtool', ('signtool',), env=env))
    env.SetDefault(SIGNTOOLFLAGS='')

    env.SetDefault(SIGN='$SIGNTOOL sign')
    env.SetDefault(SIGNFLAGS='/q /a /s "$SIGNING.STORAGE.PUBLIC" /csp "$SIGNING.STORAGE.PROVIDER" /kc "$SIGNING.STORAGE.PRIVATE"')
    env.SetDefault(SIGNCOM='$SIGN $SIGNFLAGS $SOURCES -out $TARGETS')

    env.SetDefault(SIGNING=common.namespace(USERNAME=os.getenv('USERNAME', 'unknown'),
                                            STORAGE=common.namespace(PRIVATE='codesign',
                                                                     PUBLIC='codesign',
                                                                     PROVIDER='Microsoft Strong Cryptographic Provider'),
                                            NAME='CN=$SIGNING.USERNAME,OU=$SIGNING.ORGNAME,O=$SIGNING.COMPANY,E=$SIGNING.EMAIL',
                                            ORGNAME='unknown',
                                            COMPANY='unknown',
                                            EMAIL='unknown',
                                            ENABLED=False,
                                            GENCERT=True)
                   )

    signFile = SCons.Builder.Builder(action=signAction,
                                     emitter=signEmit,
                                     target_factory=SCons.Node.FS.File,
                                     source_factory=SCons.Node.FS.Entry)

    env['BUILDERS']['SignFile'] = signFile


def exists(env):
    return msvc.Exists(env, 'signtool')
