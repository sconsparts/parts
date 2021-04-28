#
# $Id: doxygen.py 23243 2008-05-30 15:15:40Z eleskine $


import fnmatch
import os
import re
import string
import time

import SCons.Builder
import SCons.Node.FS
import SCons.Util
from SCons.Debug import Trace

t = 0


def DetectDot(env):
    res = env.Detect('dot')
    if t:
        Trace('Dot env.detected as "%s"\n' % (res))
    if res is None and SCons.Util.can_read_reg:
        # Look for it in:
        # HKLM\\Software\\ATT\\Graphviz
        try:
            (res, tmp) = SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE,
                                                r'SOFTWARE\\ATT\\Graphviz\\InstallPath')
            res = os.path.join(res, 'bin', 'dot.exe')
            if os.path.exists(res):
                if t:
                    Trace('Dot detected as "%s"\n' % res)
                env.PrependENVPath('PATH', os.path.split(res)[0])
            else:
                res = None
        except Exception:
            if t:
                Trace('An error occured during reading DOT from the registry\n')
            res = None
    return res


def DetectDoxygen(env):
    res = env.Detect('doxygen')
    # We perform search for doxygen in the $PATH and
    # in case of failure in its default locations and in
    # HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\doxygen_is1
    # 'Inno Setup: App Path'

    if t:
        Trace('Doxygen env.detected as "%s"\n' % res)
    if res is None and SCons.Util.can_read_reg:
        try:
            (res, tmp) = SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE,
                                                r'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\doxygen_is1\\InstallLocation')
            res = os.path.join(res, 'bin', 'doxygen.exe')
            if os.path.exists(res):
                if t:
                    Trace('Doxygen detected as "%s"\n' % res)
                env.PrependENVPath('PATH', os.path.split(res)[0])
                res = 'doxygen'
            else:
                res = None
        except Exception:
            if t:
                Trace('An error occured during reading DOXYGEN from the registry\n')
            res = None

    return res


def parseDoxyFile(f):
    res = {}
    r = re.compile(r"^\s*(\w+)\s*=\s*(\w*.*\w*)\s*")
    ss = f.readlines()
    if ss is None:
        return res

    for s in ss:
        s = string.lstrip(s)
        if len(s) > 0 and s[0] != '#':
            m = r.search(s)
            if not m is None and m.group(1) != '':
                v = m.group(2)
                if v == '':
                    v = None
                res[string.upper(m.group(1))] = v
    return res


class MyDir(SCons.Node.FS.Dir):

    def __init__(self, name, directory, fs):
        if t:
            Trace("MyDir.__init__\n")
        self.NodeInfo = SCons.Node.FS.FileNodeInfo
        self.BuildInfo = SCons.Node.FS.FileBuildInfo
        SCons.Node.FS.Dir.__init__(self, name, directory, fs)
        self.set_noclean(0)

    def get_csig(self):
        if t:
            Trace("MyDir.get_csig\n")
        sigs = [SCons.Util.MD5signature(self.abspath)]
        for root, dirs, files in os.walk(self.abspath):
            for f in files:
                with open(os.path.join(root, f), 'r') as f:
                    sigs.append(SCons.Util.MD5signature(f.read()))
        csig = SCons.Util.MD5collect(sigs)
        self.get_ninfo().csig = csig
        return csig

    def get_stored_info(self):
        if t:
            Trace("MyDir.get_stored_info\n")
        try:
            return self._memo['get_stored_info']
        except KeyError:
            pass

        try:
            sconsign_entry = self.dir.sconsign().get_entry(self.name)
        except (KeyError, OSError):
            import SCons.SConsign
            sconsign_entry = SCons.SConsign.SConsignEntry()
            sconsign_entry.binfo = self.new_binfo()
            sconsign_entry.ninfo = self.new_ninfo()
        else:
            from SCons.Node.FS import FileBuildInfo
            if isinstance(sconsign_entry, FileBuildInfo):
                # This is a .sconsign file from before the Big Signature
                # Refactoring; convert it as best we can.
                sconsign_entry = self.convert_old_entry(sconsign_entry)
            try:
                delattr(sconsign_entry.ninfo, 'bsig')
            except AttributeError:
                pass

        self._memo['get_stored_info'] = sconsign_entry

        return sconsign_entry

    def visited(self):
        if t:
            Trace("MyDir.visited\n")
        if self.exists():
            self.get_build_env().get_CacheDir().push_if_forced(self)

        ninfo = self.get_ninfo()

        csig = self.get_csig()
        if csig:
            ninfo.csig = csig

        ninfo.timestamp = self.get_timestamp()
        ninfo.size = 0

        if not self.has_builder():
            # This is a source file, but it might have been a target file
            # in another build that included more of the DAG.  Copy
            # any build information that's stored in the .sconsign file
            # into our binfo object so it doesn't get lost.
            old = self.get_stored_info()
            self.get_binfo().__dict__.update(old.binfo.__dict__)

        self.store_info()

    def is_up_to_date(self):
        if t:
            Trace("MyDir.is_up_to_date\n")
        if not self.exists():
            return 0
        if self.changed():
            return 0

        return self.get_csig() == self.get_stored_info().ninfo.csig

    def store_info(self):
        # Merge our build information into the already-stored entry.
        # This accomodates "chained builds" where a file that's a target
        # in one build (SConstruct file) is a source in a different build.
        # See test/chained-build.py for the use case.
        if t:
            Trace("MyDir.store_info\n")
        self.dir.sconsign().store_info(self.name, self)

    def remove(self):
        if self.exists():
            for root, dirs, files in os.walk(self.abspath, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
            os.rmdir(root)
            return 1
        return None


def createFileNode(nodename, directory=None, create=1):
    return SCons.Node.FS.get_default_fs()._lookup(nodename, directory, SCons.Node.FS.File, create)


def createDirNode(nodename, directory=None, create=1):
    return SCons.Node.FS.get_default_fs()._lookup(nodename, directory, MyDir, create)

# targets:
#   ${OUTPUT_DIRECTORY}\${HTML_OUTPUT:html}
#   ${OUTPUT_DIRECTORY}\${LATEX_OUTPUT:latex}
#   ${OUTPUT_DIRECTORY}\${RTF_OUTPUT}
#   ${OUTPUT_DIRECTORY}\${XML_OUTPUT}
#   ${OUTPUT_DIRECTORY}\${MAN_OUTPUT}
#   ${OUTPUT_DIRECTORY}\${CHM_FILE}
#   ${GENERATE_CHI}?${OUTPUT_DIRECTORY}\${CHM_FILE.chi}
#   ${WARN_LOGFILE}


def generateTargets(config, outdir):
    target = []
    if string.upper(config.get('GENERATE_HTML')) == 'YES':
        target.append(os.path.join(outdir, config.get('HTML_OUTPUT') or 'html'))
    if string.upper(config.get('GENERATE_LATEX')) == 'YES':
        target.append(os.path.join(outdir, config.get('LATEX_OUTPUT') or 'latex'))
    if string.upper(config.get('GENERATE_RTF')) == 'YES':
        target.append(os.path.join(outdir, config.get('RTF_OUTPUT') or 'rtf'))
    if string.upper(config.get('GENERATE_MAN')) == 'YES':
        target.append(os.path.join(outdir, config.get('MAN_OUTPUT') or 'man'))
    if string.upper(config.get('GENERATE_XML')) == 'YES':
        target.append(os.path.join(outdir, config.get('XML_OUTPUT') or 'xml'))
    if string.upper(config.get('GENERATE_AUTOGEN_DEF')) == 'YES':
        target.append(os.path.join(outdir, 'def'))
    if string.upper(config.get('GENERATE_PERLMOD')) == 'YES':
        target.append(os.path.join(outdir, config.get('PERLMOD_OUTPUT') or 'perlmod'))

    tagfile = config.get('GENERATE_TAGFILE')
    if not tagfile is None:
        target.append(createFileNode(tagfile))

    if string.upper(config.get('WARNINGS')) == 'YES':
        warningsfile = config.get('WARN_LOGFILE')
        if not warningsfile is None:
            target.append(createFileNode(warningsfile))

    return target


def fileMatch(f, includes, excludes):
    res = 0
    for i in includes:
        if fnmatch.fnmatch(f, i):
            res = 1
            break

    if res:
        for e in excludes:
            if fnmatch.fnmatch(f, e):
                return 0

    return res

# sources:
# Doxyfile
# *.c *.cc *.cxx *.cpp *.c++ *.java *.ii *.ixx *.ipp *.i++ *.inl *.h *.hh *.hxx
# *.hpp *.h++ *.idl *.odl *.cs *.php *.php3 *.inc *.m *.mm *.py
# -${EXCLUDE}
# -${EXCLUDE_PATTERNS}


def generateSources(config, env):

    res = []
    if string.upper(config.get('HAVE_DOT')) == 'YES':
        DetectDot(env)

    include_pattern = config.get('FILE_PATTERNS') or '''*.c *.cc *.cxx *.cpp *.c++ *.java *.ii *.ixx *.ipp
    *.i++ *.inl *.h *.hh *.hxx *.hpp *.h++ *.idl *.odl *.cs *.php *.php3 *.inc *.m *.mm *.py'''
    include_pattern = string.split(include_pattern)
    exclude_pattern = config.get('EXCLUDE_PATTERNS') or ''
    exclude_pattern = string.split(exclude_pattern)
    recursive = string.upper(config.get('RECURSIVE')) == 'YES'

    include = config.get('INPUT') or '.'
    include = string.split(include)

    exclude = config.get('EXCLUDE') or ''
    exclude = string.split(exclude)

    for e in include:
        if e in exclude:
            continue
        if os.path.isdir(e):
            if recursive:
                for root, dirs, files in os.walk(e):
                    for f in files:
                        if fileMatch(f, include_pattern, exclude_pattern):
                            res.append(os.path.join(root, f))
            else:  # !recursive
                for f in os.listdir(e):
                    if not os.path.isdir(f) and fileMatch(f, include_pattern, exclude_pattern):
                        res.append(os.path.join(e, f))
        else:  # !os.path.isdir(e)
            res.append(e)

    if t:
        Trace('Generated sources: %s\n' % str(res))
    return res


def doxyEmitter(target, source, env):
    doxyfile = env.get('DOXYFILE') or 'Doxyfile'
    source = [doxyfile]
    with file(doxyfile, 'r') as doxyfile:
        config = parseDoxyFile(doxyfile)
    outdir = config.get('OUTPUT_DIRECTORY') or '.'

    target = generateTargets(config, outdir)
    source += generateSources(config, env)

    return (target, source)


def createDoxygenBuilder(env):
    try:
        doxygen = env['BUILDERS']['Doxygen']
    except Exception:
        doxygen = SCons.Builder.Builder(
            action="$DOXYGEN $DOXYFILE",
            emitter=doxyEmitter,
            target_factory=createDirNode)
        env['BUILDERS']['Doxygen'] = doxygen
    return doxygen


def generate(env):
    env['DOXYGEN'] = DetectDoxygen(env)
    DetectDot(env)
    createDoxygenBuilder(env)


def exists(env):
    return DetectDoxygen(env)

# vim: set et ts=4 sw=4 ai ft=python :
