"""SCons.Tool.mslink

Tool-specific initialization for the Microsoft linker.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.

"""

#
# __COPYRIGHT__
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
from __future__ import absolute_import, division, print_function

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

import os.path

import parts.api.output as output
import parts.common as common
import parts.tools.Common
from parts.tools.MSCommon import msvc, validate_vars

import SCons.Action
import SCons.Defaults
import SCons.Errors
import SCons.Platform.win32
import SCons.Tool
import SCons.Util


def pdbGenerator(env, target, source, for_signature):
    try:
        return ['/PDB:%s' % target[0].attributes.pdb, '/DEBUG']
    except (AttributeError, IndexError):
        return None


def _dllTargets(target, source, env, for_signature, paramtp):
    listCmd = []
    dll = env.FindIxes(target, '%sPREFIX' % paramtp, '%sSUFFIX' % paramtp)
    if dll:
        listCmd.append("/out:%s" % dll.get_string(for_signature))

    implib = env.FindIxes(target, 'LIBPREFIX', 'LIBSUFFIX')
    if implib:
        listCmd.append("/implib:%s" % implib.get_string(for_signature))

    return listCmd


def _dllSources(target, source, env, for_signature, paramtp):
    listCmd = []

    deffile = env.FindIxes(source, "WINDOWSDEFPREFIX", "WINDOWSDEFSUFFIX")
    for src in source:
        # Check explicitly for a non-None deffile so that the __cmp__
        # method of the base SCons.Util.Proxy class used for some Node
        # proxies doesn't try to use a non-existent __dict__ attribute.
        if deffile and src == deffile:
            # Treat this source as a .def file.
            listCmd.append("/def:%s" % src.get_string(for_signature))
        else:
            # Just treat it as a generic source file.
            listCmd.append(src)
    return listCmd


def windowsShlinkTargets(target, source, env, for_signature):
    return _dllTargets(target, source, env, for_signature, 'SHLIB')


def windowsShlinkSources(target, source, env, for_signature):
    return _dllSources(target, source, env, for_signature, 'SHLIB')


def _windowsLdmodTargets(target, source, env, for_signature):
    """Get targets for loadable modules."""
    return _dllTargets(target, source, env, for_signature, 'LDMODULE')


def _windowsLdmodSources(target, source, env, for_signature):
    """Get sources for loadable modules."""
    return _dllSources(target, source, env, for_signature, 'LDMODULE')


def _dllEmitter(target, source, env, paramtp):
    """Common implementation of dll emitter."""
    validate_vars(env)

    extratargets = []
    extrasources = []

    dll = env.FindIxes(target, '%sPREFIX' % paramtp, '%sSUFFIX' % paramtp)
    no_import_lib = env.get('no_import_lib', 0)

    if not dll:
        raise SCons.Errors.UserError('A shared library should have exactly one target with the suffix: %s' % env.subst(
            '$%sSUFFIX' % paramtp))

    insert_def = env.subst("$WINDOWS_INSERT_DEF")
    if not insert_def in ['', '0', 0] and \
       not env.FindIxes(source, "WINDOWSDEFPREFIX", "WINDOWSDEFSUFFIX"):

        # append a def file to the list of sources
        extrasources.append(
            env.ReplaceIxes(dll,
                            '%sPREFIX' % paramtp, '%sSUFFIX' % paramtp,
                            "WINDOWSDEFPREFIX", "WINDOWSDEFSUFFIX"))

    #tmp = env.get('MSVC_VERSION', '6.0')
    # if tmp is None:
    #    tmp = 6.0
    #version_num = float(tmp)
    # if version_num >= 8.0 and version_num < 10 and env.get('WINDOWS_INSERT_MANIFEST', 1):
    #    # MSVC 8 and 9 automatically generates .manifest files that must be installed
    #    tmp=env.ReplaceIxes(dll,
    #                        '%sPREFIX' % paramtp, '%sSUFFIX' % paramtp,
    #                        "WINDOWSSHLIBMANIFESTPREFIX", "WINDOWSSHLIBMANIFESTSUFFIX")
    #    tmp=env.File(tmp)
    #    tmp.attributes.FilterAs=target[0]
    #    extratargets.append(tmp)

    if 'PDB' in env and env['PDB'] and not env.get('IGNORE_PDB', False):
        pdb = env.arg2nodes('$PDB', target=target, source=source)[0]
        extratargets.append(pdb)
        target[0].attributes.pdb = pdb

    # may need some tweaks still
    # if cli code is being used there is no .lib file made
    # this might be true if no .obj files are made.. need to test
    if env.FindIxes(source, "OBJPREFIX", "CLIOBJSUFFIX"):
        no_import_lib = True

    if not no_import_lib and \
       not env.FindIxes(target, "LIBPREFIX", "LIBSUFFIX"):
        # Append an import library to the list of targets.
        extratargets.append(
            env.ReplaceIxes(dll,
                            '%sPREFIX' % paramtp, '%sSUFFIX' % paramtp,
                            "LIBPREFIX", "LIBSUFFIX"))
        # and .exp file is created if there are exports from a DLL
        extratargets.append(
            env.ReplaceIxes(dll,
                            '%sPREFIX' % paramtp, '%sSUFFIX' % paramtp,
                            "WINDOWSEXPPREFIX", "WINDOWSEXPSUFFIX"))

    return (env.Precious(target + extratargets), env.Precious(source + extrasources))


def windowsLibEmitter(target, source, env):
    return _dllEmitter(target, source, env, 'SHLIB')


def ldmodEmitter(target, source, env):
    """Emitter for loadable modules.

    Loadable modules are identical to shared libraries on Windows, but building
    them is subject to different parameters (LDMODULE*).
    """
    return _dllEmitter(target, source, env, 'LDMODULE')


def prog_emitter(target, source, env):
    validate_vars(env)

    extratargets = []

    exe = env.FindIxes(target, "PROGPREFIX", "PROGSUFFIX")
    if not exe:
        raise SCons.Errors.UserError("An executable should have exactly one target with the suffix: %s" % env.subst("$PROGSUFFIX"))

    #tmp = env.get('MSVC_VERSION', '6.0')
    # if tmp is None:
    #    tmp = 6.0
    #version_num = float(tmp)
    # if version_num >= 8.0 and version_num < 10 and env.get('WINDOWS_INSERT_MANIFEST', 1):
    #    # MSVC 8 and 9 automatically generates .manifest files that must be installed
    #    tmp=env.ReplaceIxes(exe,
    #                        "PROGPREFIX", "PROGSUFFIX",
    #                        "WINDOWSPROGMANIFESTPREFIX", "WINDOWSPROGMANIFESTSUFFIX")
    #    tmp=env.File(tmp)
    #    tmp.attributes.FilterAs=target[0]
    #    extratargets.append(tmp)
    #
    if 'PDB' in env and env['PDB'] and not env.get('IGNORE_PDB', False):
        pdb = env.arg2nodes('$PDB', target=target, source=source)[0]
        extratargets.append(pdb)
        target[0].attributes.pdb = pdb

    return (env.Precious(target + extratargets), env.Precious(source))


def RegServerFunc(target, source, env):
    if 'register' in env and env['register']:
        ret = regServerAction([target[0]], [source[0]], env)
        if ret:
            raise SCons.Errors.UserError("Unable to register %s" % target[0])
        else:
            print("Registered %s sucessfully" % target[0])
        return ret
    return 0


def EmbedManifestDLLFunc(target, source, env):

    if(float(env['MSVC_VERSION']) < 8.0):
        return 0
    insert_manifest = env.get('WINDOWS_INSERT_MANIFEST', True)
    manifestSrc = str(target[0]) + '.manifest'

    if(insert_manifest and os.path.exists(manifestSrc)):
        manifest = manifestSrc
        ret = (embedManifestDLLAction)([target[0]], None, env)
        if ret:
            raise SCons.Errors.UserError("Unable to embed manifest into %s" % (target[0]))
        else:
            print("Embedded %(target)s.manifest successfully into %(target)s" % {'target': target[0]})
        return ret
    return 0


def EmbedManifestProgFunc(target, source, env):
    # test to see if the version of VC is greater than 8.0
    # as this version requires that manifest be used
    # need tests for no manifest cases for 8.0 and above (currently stupid on this)

    if(float(env['MSVC_VERSION']) < 8.0):
        return 0
    insert_manifest = env.get('WINDOWS_INSERT_MANIFEST', True)
    manifestSrc = str(target[0]) + '.manifest'

    if insert_manifest and os.path.exists(manifestSrc):
        manifest = manifestSrc
        ret = (embedManifestProgAction)(env.Precious(target[0]), None, env)
        if ret:
            raise SCons.Errors.UserError("Unable to embed manifest into %s" % (target[0]))
        else:
            print("Embedded %(target)s.manifest successfully into %(target)s" % {'target': target[0]})
        return ret
    return 0


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

# DLL's
embedManifestDLLAction = SCons.Action.Action("$EMBEDMANIFESTDLLCOM", "$EMBEDMANIFESTDLLCOMSTR")
embedManifestDLLCheck = SCons.Action.Action(EmbedManifestDLLFunc, None)

regServerAction = SCons.Action.Action("$REGSVRCOM", "$REGSVRCOMSTR")
regServerCheck = SCons.Action.Action(RegServerFunc, None)

shlibLinkAction = SCons.Action.Action(
    '${TEMPFILE("$SHLINK $SHLINKFLAGS $_SHLINK_TARGETS $_LIBDIRFLAGS $_LIBFLAGS $_PDB $_SHLINK_SOURCES $SHLINKEXFLAGS $_LIBEXFLAGS")}')
compositeShLinkAction = shlibLinkAction + embedManifestDLLCheck + signCheck + regServerCheck
ldmodLinkAction = SCons.Action.Action(
    '${TEMPFILE("$LDMODULE $LDMODULEFLAGS $_LDMODULE_TARGETS $_LIBDIRFLAGS $_LIBFLAGS $_PDB $_LDMODULE_SOURCES")}')
compositeLdmodAction = ldmodLinkAction + embedManifestDLLCheck + signCheck + regServerCheck

# programs
registerServerAction = SCons.Action.Action("REGISTEREXECOM", "$REGISTEREXECOMSTR")
registerServerCheck = SCons.Action.Action(RegServerFunc, None)
embedManifestProgAction = SCons.Action.Action("$EMBEDMANIFESTPROGCOM", "$EMBEDMANIFESTPROGCOMSTR")
embedManifestProgCheck = SCons.Action.Action(EmbedManifestProgFunc, None)

linkcomAction = SCons.Action.Action(
    '${TEMPFILE("$LINK $LINKFLAGS /OUT:$TARGET.windows $_LIBDIRFLAGS $_LIBFLAGS $_PDB $SOURCES.windows $LINKEXFLAGS $_LIBEXFLAGS")}')
compositelinkcomAction = linkcomAction + embedManifestProgCheck + signCheck + registerServerCheck


def smart_link(source, target, env, for_signature):

    has_native = env.FindIxes(source, "OBJPREFIX", "OBJSUFFIX")
    has_dotnet = env.FindIxes(source, "OBJPREFIX", "CLIOBJSUFFIX")
    #
    # if has_native and has_dotnet:
    #    return ???
    # elif has_dotnet:
    #    return ??
    # else case
    # return '$CC'


def generate(env):
    """Add Builders and construction variables for ar to an Environment."""
    SCons.Tool.createSharedLibBuilder(env)
    SCons.Tool.createProgBuilder(env)

    # Set-up ms tools paths for default version
    msvc.MergeShellEnv(env)

    env.SetDefault(_LIBEXFLAGS='${_concat(LIBLINKPREFIX, LIBEXS, LIBLINKSUFFIX, __env__)}')

    env.SetDefault(SHLINK=parts.tools.Common.toolvar('link', ('link',), env=env))
    env.SetDefault(SHLINKFLAGS=SCons.Util.CLVar('$LINKFLAGS /dll'))
    env.SetDefault(SHLINKEXFLAGS=SCons.Util.CLVar('$LINKEXFLAGS'))
    env.SetDefault(_SHLINK_TARGETS=windowsShlinkTargets)
    env.SetDefault(_SHLINK_SOURCES=windowsShlinkSources)
    env.SetDefault(SHLINKCOM=compositeShLinkAction)
    env.Append(SHLIBEMITTER=[windowsLibEmitter])
    env.SetDefault(LINK=parts.tools.Common.toolvar('link', ('link',), env=env))
    env.SetDefault(LINKFLAGS=SCons.Util.CLVar())
    env.SetDefault(_PDB=pdbGenerator)
    env.SetDefault(LINKCOM=compositelinkcomAction)
    env.Append(PROGEMITTER=[prog_emitter])
    env.SetDefault(LIBDIRPREFIX='/LIBPATH:')
    env.SetDefault(LIBDIRSUFFIX='')
    env.SetDefault(LIBLINKPREFIX='')
    env.SetDefault(LIBLINKSUFFIX='$LIBSUFFIX')

    env.SetDefault(WIN32DEFPREFIX='')
    env.SetDefault(WIN32DEFSUFFIX='.def')
    env.SetDefault(WIN32_INSERT_DEF=0)
    env.SetDefault(WINDOWSDEFPREFIX='${WIN32DEFPREFIX}')
    env.SetDefault(WINDOWSDEFSUFFIX='${WIN32DEFSUFFIX}')
    env.SetDefault(WINDOWS_INSERT_DEF='${WIN32_INSERT_DEF}')

    env.SetDefault(WIN32EXPPREFIX='')
    env.SetDefault(WIN32EXPSUFFIX='.exp')
    env.SetDefault(WINDOWSEXPPREFIX='${WIN32EXPPREFIX}')
    env.SetDefault(WINDOWSEXPSUFFIX='${WIN32EXPSUFFIX}')

    env.SetDefault(WINDOWSSHLIBMANIFESTPREFIX='')
    env.SetDefault(WINDOWSSHLIBMANIFESTSUFFIX='${SHLIBSUFFIX}.manifest')
    env.SetDefault(WINDOWSPROGMANIFESTPREFIX='')
    env.SetDefault(WINDOWSPROGMANIFESTSUFFIX='${PROGSUFFIX}.manifest')

    env.SetDefault(REGSVRACTION=regServerCheck)
    env.SetDefault(REGSVR=os.path.join(SCons.Platform.win32.get_system_root(), 'System32', 'regsvr32'))
    env.SetDefault(REGSVRFLAGS='/s ')
    env.SetDefault(REGSVRCOM='$REGSVR $REGSVRFLAGS ${TARGET.windows}')
    env.SetDefault(REGISTEREXECOM='${TARGET.windows} /regserver')

    env.SetDefault(MT=parts.tools.Common.toolvar('mt', ('mt',), env=env))
    env.SetDefault(MTFLAGS='')
    env.SetDefault(EMBEDMANIFESTDLLCOM='$MT $MTFLAGS -outputresource:${TARGET};2 -manifest ${TARGET}.manifest')
    env.SetDefault(EMBEDMANIFESTPROGCOM='$MT $MTFLAGS -outputresource:${TARGET};1 -manifest ${TARGET}.manifest')

    #env.SetDefault(MAKECERT ='makecert')
    #env.SetDefault(MAKECERTFLAGS ='-sk "$SIGNING.STORAGE.PRIVATE" -ss "$SIGNING.STORAGE.PUBLIC" -n "$SIGNING.NAME"')
    #env.SetDefault(MAKECERTCOM ='$MAKECERT $MAKECERTFLAGS')

    #env.SetDefault(SIGNTOOL =parts.tools.Common.toolvar('signtool', ('signtool',), env = env))
    #env.SetDefault(SIGNTOOLFLAGS ='')

    #env.SetDefault(SIGN ='$SIGNTOOL sign')
    #env.SetDefault(SIGNFLAGS ='/q /a /s "$SIGNING.STORAGE.PUBLIC" /csp "$SIGNING.STORAGE.PROVIDER" /kc "$SIGNING.STORAGE.PRIVATE"')
    #env.SetDefault(SIGNCOM ='$SIGN $SIGNFLAGS "$TARGET"')

    # env.SetDefault(SIGNING =common.namespace(USERNAME = os.getenv('USERNAME', 'unknown'),
    #                                  STORAGE = common.namespace(PRIVATE = 'codesign',
    #                                                             PUBLIC = 'codesign',
    #                                                             PROVIDER = 'Microsoft Strong Cryptographic Provider'),
    #                                  NAME = 'CN=$SIGNING.USERNAME,OU=$SIGNING.ORGNAME,O=$SIGNING.COMPANY,E=$SIGNING.EMAIL',
    #                                  ORGNAME = 'unknown',
    #                                  COMPANY = 'unknown',
    #                                  EMAIL = 'unknown',
    #                                  ENABLED = False,
    #                                  GENCERT = True)
    #               )

    # Loadable modules are on Windows the same as shared libraries, but they
    # are subject to different build parameters (LDMODULE* variables).
    # Therefore LDMODULE* variables correspond as much as possible to
    # SHLINK*/SHLIB* ones.
    SCons.Tool.createLoadableModuleBuilder(env)
    env.SetDefault(LDMODULE='$SHLINK')
    env.SetDefault(LDMODULEPREFIX='$SHLIBPREFIX')
    env.SetDefault(LDMODULESUFFIX='$SHLIBSUFFIX')
    env.SetDefault(LDMODULEFLAGS='$SHLINKFLAGS')
    env.SetDefault(_LDMODULE_TARGETS=_windowsLdmodTargets)
    env.SetDefault(_LDMODULE_SOURCES=_windowsLdmodSources)
    env.SetDefault(LDMODULEEMITTER=[ldmodEmitter])
    env.SetDefault(LDMODULECOM=compositeLdmodAction)

    #api.output.print_msg("Configured Tool %s\t for version <%s> target <%s>"%('mslink',env['MSVC']['VERSION'],env['TARGET_PLATFORM']))


def exists(env):
    return msvc.Exists(env, 'link')

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
