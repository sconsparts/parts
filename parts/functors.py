import glb
import common
import core.util
import api.output
import requirement

import SCons.Script

import thread

from SCons.Debug import logInstanceCreation


def gen_rpath_link(sec):
    '''
    Add the Rlink path that would be added for the component depending on this
    component, Not what this component would depend on
    '''
    import mappers

    dlst = sec.Depends
    env = sec.Env
    rplst = []

    # setup the current alias case
    # this adds what this componnet directly depends on
    # not what it dependents depend on which is what we need for the
    # rpath-link case
    # get the libpath for this component
    plist = mappers.sub_lst(env, env.get('LIBPATH', []), thread.get_ident(), recurse=False)
    plist = env.Flatten(plist)
    for p in plist:
        rp = '-Wl,-rpath-link=' + env.Dir(p).path
        common.append_unique(rplst, rp)

    # setup everything that we depend on that we may not have added yet
    for d in dlst:
        # make sure we depend on a LIBPATH value of this component
        if requirement.REQ.LIBPATH not in d.Requires:
            pass
        elif d.PartRef.hasUniqueMatch:
            try:
                # try to get a cached value
                rtmp = d.Section.Exports['rlink']
            except KeyError:
                # generate the values
                rtmp = gen_rpath_link(d.Section)

            for i in rtmp:
                common.append_unique(rplst, i)
            sec.Exports['rlink'] = rplst

        elif d.PartRef.hasMatch == False:
            api.output.warning_msg("Failed to map dependency for {0} when mapping -rpath-link data because:\n {1}".format(
                sec.Part.Name, d.PartRef.NoMatchStr()), show_stack=False)
        elif d.PartRef.hasAmbiguousMatch:
            api.output.warning_msg("Failed to map dependency for {0} when mapping -rpath-link data because:\n {1}".format(
                sec.Part.Name, d.PartRef.NoMatchStr()), show_stack=False)
    return rplst


class map_rpath_link_part(object):
    ''' this class is used to map the rpath-link option to the LINKFLAGS on linux
    like systems by pulling information of the LIBPATH.
    '''

    def __init__(self, env, sec):
        if __debug__:
            logInstanceCreation(self)
        self.env = env
        self.sec = sec

    def __call__(self):
        if self.env['AUTO_RPATH'] == True:
            rplst = gen_rpath_link(self.sec)
            self.env.AppendUnique(LINKFLAGS=rplst, delete_existing=True)


class map_rpath_part(object):
    '''This class adds to the RPATH value based on location of where there .SO
    are stored.. classically in a seperate INSTALL_LIB directory. This allow for correct
    running of the program after a build without special setup'''

    def __init__(self, env, add_self=False):
        if __debug__:
            logInstanceCreation(self)
        self.env = env
        self.add_self = add_self

    def __call__(self):
        # do we want to auto generate RPATH information
        if self.env['AUTO_RPATH'] == True:
            rlst = self.env.get('RPATH', [])
            # make a mapping between the bin and lib directories
            if self.env['HOST_OS'] == 'win32':
                quote = '"'
            else:
                quote = "'"
            rlst.append(self.env.Literal('{0}$$ORIGIN/{1}{0}'.format(quote, self.env.Dir('$INSTALL_BIN').rel_path(
                self.env.Dir('$INSTALL_LIB')))))
            self.env['RPATH'] = rlst


class map_build_context(object):
    '''
        This maps all build info related files we might need to help detect quickly
    if the build context has changed from the last run.
    '''

    def __init__(self, pobj):
        if __debug__:
            logInstanceCreation(self)
        self.pobj = pobj

    def __call__(self):

        self.pobj._build_context_files.update(self.pobj.Env['_BUILD_CONTEXT_FILES'])
        self.pobj._config_context_files.update(self.pobj.Env['_CONFIG_CONTEXT'])


class map_depends(object):

    def __init__(self, env, partref, tsection, requiements, stack):
        if __debug__:
            logInstanceCreation(self)
        self.env = env
        self.partref = partref
        self.tsection = tsection
        self.requiements = requiements
        self.stack = stack

    def __call__(self):
        if self.partref.hasUniqueMatch:
            dep_pobj = self.partref.Matches[0]
            dep_sec = dep_pobj.Section(self.tsection)
        elif self.partref.hasMatch == False:
            api.output.error_msg("Failed to map dependency for {0} because:\n {1}".format(
                self.env.subst('$PART_NAME'), self.partref.NoMatchStr()), stackframe=self.stack)
        elif self.partref.hasAmbiguousMatch:
            api.output.error_msg("Failed to map dependency for {0} because:\n {1}".format(
                self.env.subst('$PART_NAME'), self.partref.AmbiguousMatchStr()), stackframe=self.stack)
        # print "filling in","{0}::alias::{1}".format(self.env['PART_SECTION'],self.env['PART_ALIAS']),"\t",dep_sec.ID
        # print " ",dep_sec.Exports.keys()
        # dep_sec.esigs()
        alias = "{0}::alias::{1}".format(self.env['PART_SECTION'], self.env['PART_ALIAS'])
        for r in self.requiements:
            key = r.key
            if "INSTALL" in key or "SDK" in key:  # dep_sec.Exports.get(key):
                alias1 = "{0}::alias::{1}::{2}".format(self.env['PART_SECTION'], self.env['PART_ALIAS'], key)
                alias2 = "{0}::alias::{1}::{2}".format(self.tsection, dep_pobj.Alias, key)
                self.env.Alias(alias, self.env.Alias(alias1))
                self.env.Alias(alias1, self.env.Alias(alias2))


# add configuartion varaible
api.register.add_bool_variable('AUTO_RPATH', True, 'Controls if RPath values are automatically added to path')
