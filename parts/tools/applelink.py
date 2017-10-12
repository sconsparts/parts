import SCons.Tool.applelink as applelink
import SCons.Action

from parts.tools.gnulink import _pdbResolveString
from parts.tools.Common import toolvar


def _pdbEmitter(target, source, env):
    # TODO : The following almost cut/pasted from parts/tool/gnulink.py. Consider re-factoring
    if env.get('PDB') and not env.get('IGNORE_PDB', False):
        # Mac OS strictly requires symbol file names to end with ".dSYM"
        name = target[0].name + '.dSYM'
        pdb = target[0].Dir(name)
        pdb.File('Contents/Info.plist')
        pdb.File('Contents/Resources/DWARF/regular_with_pdb')
        target[0].attributes.pdb = pdb

        # For correct handling pdb files with InstallTarget function
        # we have to know how to treat it: like executable or like SO
        # To determine this the function will look at pdb's FilterAs attribute
        pdb.attributes.FilterAs = target[0]
        target.append(pdb)
    return target, source


def _setUpPdbActions(env):
    if not env.Detect('$DSYMUTIL'):
        # If there are no dsymutil tool on the system we cannot create .dSYMs.
        parts.api.output.warning_msg(
            "dsymutil tool is not found on your system. "
            "Separate debug files will not be created"
        )
        return env

    # Actions to be appended to Program and SharedLibrary builders

    env['_pdbResolveString'] = _pdbResolveString

    env['_pdbAction'] = "$DSYMUTIL --out=${TARGET.attributes.pdb} $PDBFLAGS ${TARGET}"
    env['_pdbActionString'] = 'Creating separate debug info file for ${TARGET}'

    env['PDB_ACTION'] = SCons.Action.CommandAction(
        '${_pdbResolveString(TARGETS, _pdbAction)}',
        cmdstr='${_pdbResolveString(TARGETS, _pdbActionString)}'
    )

    env['PDB_EMITTER'] = _pdbEmitter

    env.Append(LINKCOM=['$PDB_ACTION'])
    env.Append(PROGEMITTER=[_pdbEmitter])
    env.Append(SHLINKCOM=['$PDB_ACTION'])
    env.Append(SHLIBEMITTER=[_pdbEmitter])

    return env


def generate(env):
    applelink.generate(env)

    env.SetDefault(
        DSYMUTIL=toolvar('dsymutil', ('dsymutil',), env=env),
    )

    _setUpPdbActions(env)

exists = applelink.exists

# vim: set et ts=4 sw=4 ai :
