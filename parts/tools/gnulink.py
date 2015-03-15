"""
This file is a proxy for SCons.Tool.gnulink. It forwards calls to generate and exists
functions to appropriate ones in SCons.Tool.gnulink module.

The purpose of this module to add ability to generate separate debug files (pdbs) on Linux
as well as add ability to strip resulting binaries.

This module introduces two environment variables to control binary stripping and pdbs creation:

    NO_STRIP, default value is True, this variable controls binary stripping.
        By default all binaries are not stripped. To strip binaries set this variable to
        False.

    PDB, default value not defined. Controls creation of pdb file for specified
        binary. Set its value to pdb's file name where to move debug information
        from the binary. All binaries with separate debug files will be stripped.

"""

import SCons.Tool.gnulink
import SCons.Tool.mingw
import SCons.Action
import parts.api.output
import parts.tools.GnuCommon
import parts.tools.Common

def _pdbEmitter(target, source, env):
    """
    Emitter to generate pdb File node.
    This function is called by SCons infrastructure at the moment when
    either Program or SharedLibrary function is called by particular *.parts file.

    The function expects that target parameter is a list, first element of which is
    a Node object representing either executable or shared object to be built.

    The function expands a target Node list with File object representing a
    separate debug file for the target binary with name specified in PDB
    environment variable.
    """
    # The following three lines are copy/pasted from SCons/Tool/mslink.py
    if env.has_key('PDB') and env['PDB'] and not env.get('IGNORE_PDB',False):
        pdb = env.arg2nodes('$PDB', target=target, source=source)[0]
        target[0].attributes.pdb = pdb

        # For correct handling pdb files with InstallTarget function
        # we have to know how to treat it: like executable or like SO
        # To determine this the function will look at pdb's FilterAs attribute
        pdb.attributes.FilterAs = target[0]
        target.append(pdb)
    return target, source

def _pdbResolveString(targets, template):
    """
    This function is called by SCons via env.subst magic at the moment when targets are
    about to be built. Its purpose is to decide whether a command related to pdb creation
    should be generated.

    targets is a list of Node objects the first one of which is path to binary to be built.

    template is a string to be expanded to a command which later will be executed by SCons.
    """
    try:
        if targets[0].attributes.pdb:
            return template
    except (AttributeError, IndexError):
        return ""

def _stripResolveString(env, target, template):
    """
    This function is called by SCons via env.subst magic at the moment when targets are
    about to be built. Its purpose is to decide whether a command related to binary stripping
    should be generated.

    env is environment in context of which the resulting command will be executed

    targets is a list of Node objects the first one of which is path to binary to be built.

    template is a string to be expanded to a command which later will be executed by SCons.
    """
    try:
        try:
            if target[0].attributes.pdb:
                # Always strip the binary if there should be created a pdb for it
                return template
        except AttributeError:
            # The binary has no pdb associated with it. Check NO_STRIP flag.
            if not env.get('NO_STRIP', True):
                return template
    except IndexError:
        pass
    return ""

def _setUpPdbActions(env):
    """
    The function modifies the environment by adding PDB/stripping specific actions.
    """
    if not env.Detect('$OBJCOPY'):
        # If there are no objcopy utility on the system we cannot create pdbs.
        parts.api.output.warning_msg(
            "objcopy tool is not found on your system. " \
            "Separate debug files will not be created"
        )
        return env

    env['_pdbResolveString'] = _pdbResolveString
    env['_stripResolveString'] = _stripResolveString


    env['_pdbAction'] = "$OBJCOPY --only-keep-debug $PDBFLAGS ${TARGET} ${TARGET.attributes.pdb}"
    env['_pdbActionString'] = 'Creating PDB for ${TARGET}'

    if env.get('CHMODVALUE'):
        if env.Detect("chmod"):
            env['_pdbChmodAction'] = "chmod $CHMODVALUE ${TARGET.attributes.pdb}"
        else:
            env['_pdbChmodAction'] = ""
            if env['TARGET_PLATFORM'] != 'win32':
             parts.api.output.warning_msg(
                "chmod tool is not found on your system. " \
                "Separate debug files created may have wrong permission bits"
            )
    env['_pdbChmodActionString'] = 'Changing ${TARGET.attributes.pdb} flags to $CHMODVALUE'

    env['_pdbStripAction'] = "$OBJCOPY --strip-unneeded ${TARGET}"
    env['_pdbStripActionString'] = "Stripping ${TARGET}"

    env['_pdbGnuDebugLinkAction'] = "$OBJCOPY --add-gnu-debuglink=${TARGET.attributes.pdb} ${TARGET}"
    env['_pdbGnuDebugLinkActionString'] = "Linking ${TARGET} to ${TARGET.attributes.pdb}"

    env['PDB_CREATE_ACTION'] = SCons.Action.CommandAction(
        '${_pdbResolveString(TARGETS, _pdbAction)}',
        cmdstr = '${_pdbResolveString(TARGETS, _pdbActionString)}'
        )
    env['PDB_CHMOD_ACTION'] = SCons.Action.CommandAction(
        '${_pdbResolveString(TARGETS, _pdbChmodAction)}',
        cmdstr = '${_pdbResolveString(TARGETS, _pdbChmodActionString)}'
        )
    env['STRIP_ACTION'] = SCons.Action.CommandAction(
        '${_stripResolveString(__env__, TARGETS, _pdbStripAction)}',
        cmdstr = '${_stripResolveString(__env__, TARGETS, _pdbStripActionString)}'
        )
    env['PDB_GNU_DEBUGLINK_ACTION'] = SCons.Action.CommandAction(
        '${_pdbResolveString(TARGETS, _pdbGnuDebugLinkAction)}',
        cmdstr = '${_pdbResolveString(TARGETS, _pdbGnuDebugLinkActionString)}'
        )

    # Actions to be appended to Program and SharedLibrary builders
    env['PDB_ACTION'] = SCons.Action.ListAction([
        '$PDB_CREATE_ACTION',
        '$PDB_CHMOD_ACTION',
        '$STRIP_ACTION',
        '$PDB_GNU_DEBUGLINK_ACTION',
    ])

    env['PDB_EMITTER'] = _pdbEmitter

    env.Append(LINKCOM = ['$PDB_ACTION'])
    env.Append(PROGEMITTER = [_pdbEmitter])
    env.Append(SHLINKCOM = ['$PDB_ACTION'])
    env.Append(SHLIBEMITTER = [_pdbEmitter])

    return env



def generate(env):
    """
    Proxy for SCons.Tool.gnulink.generate function.
    After call to SCons.Tool.gnulink.generate this function calls this module
    private _setUpPdbActions function which in its turn adds pdb creation/binary stripping
    actions to the environment
    """

    env['LIBPREFIX']      = 'lib'
    env['LIBSUFFIX']      = '.a'
    env['SHLIBPREFIX']    = 'lib'
    env['SHLIBSUFFIX']    = '.so'
    env['CHMODVALUE']     = '644'

    # this is a hard set.. normally handled by scons platform logic
    # but for win32 hosts it gets the values wrong ( it assumes .a only)
    env['LIBSUFFIXES']    = [ '$LIBSUFFIX', '$SHLIBSUFFIX' ]

    parts.tools.GnuCommon.binutils.setup(env)
    env['OBJCOPY'] = parts.tools.Common.toolvar(env.get('BINUTILS', {}).get('OBJCOPY', env.get('OBJCOPY', 'objcopy')), ('objcopy',), env = env)
    SCons.Tool.gnulink.generate(env)

    # Sometimes we have to use specific tools and command lines.
    # For example when building Android executables on Windows host
    try:
        env.AppendUnique(LINKFLAGS=['-B{0}'.format(env['BINUTILS'].INSTALL_ROOT)])
        env['CHMODVALUE'] = env.get('BINUTILS', {}).get('CHMODVALUE', env['CHMODVALUE'])
        env['LINKCOM'] = env.get('BINUTILS', {}).get('LINKCOM', env.get('LINKCOM'))
        env['SHLINKCOM'] = env.get('BINUTILS', {}).get('SHLINKCOM', env.get('SHLINKCOM'))
        env['__RPATH'] = env.get('BINUTILS', {}).get('__RPATH', env.get('__RPATH'))
        env['RPATHPREFIX'] = env.get('BINUTILS', {}).get('RPATHPREFIX', env.get('RPATHPREFIX'))
    except KeyError:
        pass

    if env['TARGET_OS']=='win32':
        # this is a mingw based build.
        env['SHLINKCOM']   = SCons.Tool.mingw.shlib_action
        env['LDMODULECOM'] = SCons.Tool.mingw.shlib_action
        env.Append(SHLIBEMITTER = [SCons.Tool.mingw.shlib_emitter])
        env['SHLIBSUFFIX']    = '.dll'

    _setUpPdbActions(env)

def exists(env):
    """
    Proxy for SCons.Tool.gnulink.exists function.
    """
    if env.has_key('BINUTILS_VERSION'):
        parts.tools.GnuCommon.binutils.MergeShellEnv(env)

    return SCons.Tool.gnulink.exists(env)

# vim: set et ts=4 sw=4 ai ft=python :

