# an enhanced Command function
# that also accepts target scanners


import parts.api as api
import SCons.Builder
import SCons.Scanner.Prog
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment


def CCommand(self, target, source, action, **kw):
    """This is basically Command() with target_scanner """
    bkw = {
        'action': action,
        'target_factory': self.fs.Entry,
        'source_factory': self.fs.Entry,
    }
    try:
        bkw['source_scanner'] = kw['source_scanner']
    except KeyError:
        pass
    else:
        del kw['source_scanner']
    try:
        bkw['target_scanner'] = kw['target_scanner']
    except KeyError:
        pass
    else:
        del kw['target_scanner']
    # source factory
    try:
        bkw['source_factory'] = kw['source_factory']
    except KeyError:
        pass
    else:
        del kw['source_factory']
    # target factory
    try:
        bkw['target_factory'] = kw['target_factory']
    except KeyError:
        pass
    else:
        del kw['target_factory']
    bld = SCons.Builder.Builder(**bkw)
    return bld(self, target, source, **kw)


api.register.add_global_parts_object('ProgramScanner', SCons.Scanner.Prog.ProgramScanner())
api.register.add_global_object('ProgramScanner', SCons.Scanner.Prog.ProgramScanner())

# adding logic to Scons Enviroment object
SConsEnvironment.CCommand = CCommand
