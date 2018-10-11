from parts.tools.Common.ToolSetting import ToolSetting
from parts.tools.Common.ToolSetting import MatchVersionNumbers
from parts.tools.Common.ToolInfo import ToolInfo
from parts.tools.Common.Finders import PathFinder
from parts.platform_info import SystemPlatform
from parts.tools.MSCommon import validate_vars
import parts.tools.mslink

import SCons.Util
from SCons.Scanner.Prog import print_find_libs
import os

import parts.api.output as output
import parts.tools.Common

WDK = ToolSetting('WDK')

hosts = [SystemPlatform('win32', 'any')]
targets = [SystemPlatform('win32', 'any')]

if SCons.Util.can_read_reg:
    def openRegistryKey(key, subkey):
        """
        The problem is that this code may be run on Windows x86 and on Windows Intel64.
        The registry has two branches for HKEY_LOCAL_MACHINE\Software: one is it and
        the other is WOW6432Node.
        The function tries to open the subkey in both branches.

        For info on the magic numbers used in this function look for
        'Accessing an Alternate Registry View' article in
        Microsoft Platform SDK documentation.
        """

        try:
            return SCons.Util.RegOpenKeyEx(key, subkey, 0, SCons.Util.hkey_mod.KEY_READ)
        except:
            pass

        try:
            return SCons.Util.RegOpenKeyEx(key, subkey, 0, SCons.Util.hkey_mod.KEY_READ | 0x0100)
        except:
            pass

        try:
            return SCons.Util.RegOpenKeyEx(key, subkey, 0, SCons.Util.hkey_mod.KEY_READ | 0x0200)
        except:
            pass

        return None

    def enumRegistryKey(key, i):
        try:
            return SCons.Util.RegEnumKey(key, i)
        except:
            return None

    def readRegistryValue(key, value):
        try:
            return SCons.Util.RegQueryValueEx(key, value)[0]
        except:
            return None

    class WdkScanner:
        # Versions is a dictionary of form {Major0 : {Minor0: {Build0: path}, Minor1: path}}
        versions = None
        plain_versions = None

        def __init(self):
            pass

        def _plainVersions(self):
            def _walkDict(dictionary):
                """ return list of tuples of form ('Major.Minor.Build': 'path') """
                assert isinstance(dictionary, dict)
                res = []
                for key in dictionary.keys():
                    value = dictionary[key]
                    if not isinstance(value, dict):
                        res.append((str(key), value))
                    else:
                        for tuple in _walkDict(value):
                            res.append(("%s.%s" % (str(key), tuple[0]), tuple[1]))
                return res
            assert WdkScanner.versions is not None
            if WdkScanner.plain_versions is None:
                WdkScanner.plain_versions = _walkDict(WdkScanner.versions)
            return WdkScanner.plain_versions

        def _lookInConfiguredKits(self):
            key = openRegistryKey(SCons.Util.HKEY_LOCAL_MACHINE, r"Software\Microsoft\KitSetup\configured-kits")

            if key is None:
                return None
            for i in range(0, 10000):
                s = enumRegistryKey(key, i)
                if s is None:
                    break

                subkey = openRegistryKey(key, s)
                if subkey is None:
                    continue

                for j in range(0, 10000):
                    k = enumRegistryKey(subkey, j)
                    if k is None:
                        break
                    subsubkey = openRegistryKey(subkey, k)
                    if subsubkey is None:
                        continue
                    dir = readRegistryValue(subsubkey, 'setup-install-location')
                    if dir is None:
                        continue
                    dir = os.path.normpath(dir)
                    version = os.path.basename(dir)
                    if version is unicode:
                        version = version.encode('ascii', 'ignore')
                    version = version.split('.')
                    dictionary = WdkScanner.versions
                    for n in range(len(version) - 1):
                        if version[n] not in dictionary:
                            dictionary[version[n]] = {}
                        dictionary = dictionary[version[n]]
                    dictionary[version[-1]] = dir

        def _lookInWinDDK(self):
            key = openRegistryKey(SCons.Util.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\WINDDK")
            if key is not None:
                for i in range(0, 10000):
                    s = enumRegistryKey(key, i)
                    if s is None:
                        break
                    k = openRegistryKey(key, s)
                    if k is None:
                        continue
                    dir = readRegistryValue(k, 'LFNDirectory')
                    if dir is None:
                        continue
                    dir = os.path.normpath(dir)
                    version = s
                    if version is unicode:
                        version = version.encode('ascii', 'ignore')
                    version = version.split('.')
                    if len(version) == 0:
                        continue

                    dictionary = WdkScanner.versions
                    for n in range(0, len(version) - 1):
                        if version[n] not in dictionary:
                            dictionary[version[n]] = {}
                        dictionary = dictionary[version[n]]
                    dictionary[version[-1]] = dir

        def scan(self):
            if WdkScanner.versions is None:
                WdkScanner.versions = {}
                self._lookInConfiguredKits()
                self._lookInWinDDK()
            res = {}
            for k, v in self._plainVersions():
                res[k] = os.path.join(v, 'bin')
            return res

        def resolve(self, version):
            res = self.scan()
            for k in res.keys():
                if MatchVersionNumbers(version, k):
                    return res[k]
            return None

        def resolve_version(self, version):
            for k in self.scan().keys():
                if MatchVersionNumbers(version, k):
                    return k
            return None

    def _resolveWdkDir(version):
        try:
            value = WdkScanner.versions
            for v in version.split('.'):
                value = value[v]
            return value
        except:
            return None

    class WdkInfo(ToolInfo):

        def __init__(self):
            ToolInfo.__init__(self, '*', WdkScanner(), False,
                              subst_vars={
                '_resolveWdkDir': _resolveWdkDir,
                'DIR': '${WDK._resolveWdkDir(WDK.VERSION)}',
                'TOOL': 'setenv.bat',
            },
                shell_vars={
                'WDK_DIR': '${WDK.DIR}',
                'PATH': r'${WDK.DIR}\bin',
            },
                test_file='setenv.bat'
            )

        def version_set(self):
            return set([x for x in self.install_root.scan().keys()])

        def resolve_version(self, version):
            return self.install_root.resolve_version(version)

WDK.Register(hosts=hosts, targets=targets, info=WdkInfo())


def _pdbEmitter(target, source, env):
    extratargets = []
    if 'PDB' in env and env['PDB'] and not env.get('IGNORE_PDB', False):
        pdb = env.arg2nodes('$PDB', target=target, source=source)[0]
        extratargets.append(pdb)
        target[0].attributes.pdb = pdb

    return (env.Precious(target + extratargets), env.Precious(source))


def _ddkplatform(platform):
    try:
        return {
            'x86': 'x86',
            'x86_64': 'amd64',
            'ia64': 'ia64',
        }[platform]
    except:
        return platform


def _ddklibplatform(platform):
    try:
        return {
            'x86': 'i386',
            'x86_64': 'amd64',
            'ia64': 'ia64',
        }[platform]
    except:
        return platform


def _resolve_wdk_flags(env, flags):
    min_win_ver = {
        # Windows XP
        'wxp': 'wxp',
        '5.01': 'wxp',
        5.01: 'wxp',
        501: 'wxp',
        # Windows Server 2003
        'wnet': 'wnet',
        '5.02': 'wnet',
        5.02: 'wnet',
        502: 'wnet',
        # Windows Vista and Windows Server 2008
        'wlh': 'wlh',
        '6.00': 'wlh',
        6.00: 'wlh',
        600: 'wlh',
        # Windows 7
        'win7': 'win7',
        '6.01': 'win7',
        6.01: 'win7',
        601: 'win7',
    }.get(env.get('DDK_MIN_WIN') or env.get('TARGET_VARIANT')) or 'wxp'
    res = []
    flags = env.get(flags.lower())
    if isinstance(flags, list):
        for flag in flags:
            if isinstance(flag, dict):
                try:
                    l = flag[min_win_ver]
                    if not isinstance(l, list):
                        l = [l]
                    res += l
                except KeyError:
                    pass
    return res


# Actions for DDK stuff
ASAction = SCons.Action.Action("$DDKASCOM", "$DDKASCOMSTR")
CAction = SCons.Action.Action("$DDKCCCOM", "$DDKCCCOMSTR")
ShCAction = SCons.Action.Action("$DDKSHCCCOM", "$DDKSHCCCOMSTR")
CXXAction = SCons.Action.Action("$DDKCXXCOM", "$DDKCXXCOMSTR")
ShCXXAction = SCons.Action.Action("$DDKSHCXXCOM", "$DDKSHCXXCOMSTR")

LinkAction = SCons.Action.Action("$DDKLINKCOM", "$DDKLINKCOMSTR")
ShLinkAction = SCons.Action.Action("$DDKSHLINKCOM", "$DDKSHLINKCOMSTR")

ASSuffixes = ['.s', '.asm', '.ASM']
CSuffixes = ['.c', '.C']
CXXSuffixes = ['.cc', '.cpp', '.cxx', '.c++', '.C++']


def DriverScanner(**kw):
    """Return a prototype Scanner instance for scanning executable
    files for static-lib dependencies"""
    kw['path_function'] = SCons.Scanner.FindPathDirs('DDKLIBPATH')
    ps = SCons.Scanner.Base(get_scan(kw.pop('DDKLIBS', 'DDKLIBS')), "DriverScanner", **kw)
    return ps


def get_scan(DDKLIBS='DDKLIBS'):
    def scan(node, env, libpath=()):
        """
        This scanner scans program files for static-library
        dependencies.  It will search the LIBPATH environment variable
        for libraries specified in the LIBS variable, returning any
        files it finds as dependencies.
        """
        try:
            libs = env[DDKLIBS]
        except KeyError:
            # There are no LIBS in this environment, so just return a null list:
            return []
        if SCons.Util.is_String(libs):
            libs = libs.split()
        else:
            libs = SCons.Util.flatten(libs)

        try:
            prefix = SCons.Util.flatten(env['DDKLIBPREFIXES'])
        except KeyError:
            prefix = ['']

        try:
            suffix = SCons.Util.flatten(env['DDKLIBSUFFIXES'])
        except KeyError:
            suffix = ['']

        pairs = []
        for suf in map(env.subst, suffix):
            for pref in map(env.subst, prefix):
                pairs.append((pref, suf))

        result = []

        if callable(libpath):
            libpath = libpath()

        find_file = SCons.Node.FS.find_file
        adjustixes = SCons.Util.adjustixes
        for lib in libs:
            if SCons.Util.is_String(lib):
                lib = env.subst(lib)
                for pref, suf in pairs:
                    l = adjustixes(lib, pref, suf)
                    l = find_file(l, libpath, verbose=print_find_libs)
                    if l:
                        result.append(l)
            else:
                result.append(lib)

        return result
    return scan


def createStaticLibBuilder(env):
    try:
        static_lib = env['BUILDERS']['DriverStaticLibrary']
    except KeyError:
        action_list = [SCons.Action.Action("$DDKARCOM", "$DDARCOMSTR")]

        static_lib = SCons.Builder.Builder(action=action_list,
                                           emitter='$DDKLIBEMITTER',
                                           prefix='$DDKLIBLINKPREFIX',
                                           suffix='$DDKLIBLINKSUFFIX',
                                           src_suffix='$DDKOBJSUFFIX',
                                           src_builder='DriverObject')
        env['BUILDERS']['DriverStaticLibrary'] = static_lib
        env['BUILDERS']['DriverLibrary'] = static_lib

    return static_lib


def createSharedLibBuilder(env):

    try:
        shared_lib = env['BUILDERS']['DriverSharedLibrary']
    except KeyError:
        import SCons.Defaults
        action_list = [SCons.Defaults.SharedCheck,
                       ShLinkAction]
        shared_lib = SCons.Builder.Builder(action=action_list,
                                           emitter="$DDKSHLIBEMITTER",
                                           prefix='$DDKSHLIBPREFIX',
                                           suffix='$DDKSHLIBSUFFIX',
                                           target_scanner=DriverScanner(DDKLIBS='DDKSHLIBS'),
                                           src_suffix='$DDKOBJSUFFIX',
                                           src_builder='DriverObject')
        env['BUILDERS']['DriverSharedLibrary'] = shared_lib

    return shared_lib


def _dllEmitter(target, source, env):
    """Common implementation of dll emitter."""
    validate_vars(env)

    extratargets = []
    extrasources = []

    dll = env.FindIxes(target, 'DDKSHLIBPREFIX', 'DDKSHLIBSUFFIX')
    no_import_lib = env.get('no_import_lib', 0)

    if not dll:
        raise SCons.Errors.UserError('A shared library should have exactly one target with the suffix: %s' % env.subst(
            '$DDKSHLIBSUFFIX'))

    insert_def = env.subst("$WINDOWS_INSERT_DEF")
    if not insert_def in ['', '0', 0] and \
       not env.FindIxes(source, "WINDOWSDEFPREFIX", "WINDOWSDEFSUFFIX"):

        # append a def file to the list of sources
        extrasources.append(
            env.ReplaceIxes(dll,
                            'DDKSHLIBPREFIX', 'DDKSHLIBSUFFIX',
                            "WINDOWSDEFPREFIX", "WINDOWSDEFSUFFIX"))

    if env.get('PDB') and not env.get('IGNORE_PDB', False):
        pdb = env.arg2nodes('$PDB', target=target, source=source)[0]
        extratargets.append(pdb)
        target[0].attributes.pdb = pdb

    if not no_import_lib and \
       not env.FindIxes(target, "DDKLIBPREFIX", "DDKLIBSUFFIX"):
        # Append an import library to the list of targets.
        extratargets.append(
            env.ReplaceIxes(dll,
                            'DDKSHLIBPREFIX', 'DDKSHLIBSUFFIX',
                            "LIBPREFIX", "LIBSUFFIX"))
        # and .exp file is created if there are exports from a DLL
        extratargets.append(
            env.ReplaceIxes(dll,
                            'DDKSHLIBPREFIX', 'DDKSHLIBSUFFIX',
                            "WINDOWSEXPPREFIX", "WINDOWSEXPSUFFIX"))

    return (env.Precious(target + extratargets), env.Precious(source + extrasources))


def createDriverBuilder(env):
    try:
        driverBuilder = env['BUILDERS']['WinDriver']
    except KeyError:
        driverBuilder = SCons.Builder.Builder(
            action=LinkAction,
            emitter='$DDKDRVEMITTER',
            prefix='$DDKDRVPREFIX',
            suffix='$DDKDRVSUFFIX',
            src_suffix='$DDKOBJSUFFIX',
            src_builder='DriverObject',
            target_scanner=DriverScanner())
        env['BUILDERS']['WinDriver'] = driverBuilder

    return driverBuilder


def createDriverObjectBuilder(env):
    try:
        driverObjectBuilder = env['BUILDERS']['DriverObject']
    except KeyError:
        driverObjectBuilder = SCons.Builder.Builder(
            action={},
            emiter={},
            prefix='$DDKOBJPREFIX',  # ''
            suffix='$DDKOBJSUFFIX',  # '.dobj'
            src_builder=['CFile', 'CXXFile'],
            source_scanner=SCons.Tool.SourceFileScanner,
            single_source=1)
        env['BUILDERS']['DriverObject'] = driverObjectBuilder

    return driverObjectBuilder


def createBuilders(env):
    return createDriverBuilder(env), createDriverObjectBuilder(env)


def generate(env):

    drvBuilder, drvObjBuilder = createBuilders(env)

    for suffix in ASSuffixes:
        drvObjBuilder.add_action(suffix, ASAction)

    for suffix in CSuffixes:
        drvObjBuilder.add_action(suffix, CAction)

    for suffix in CXXSuffixes:
        drvObjBuilder.add_action(suffix, CXXAction)

    createSharedLibBuilder(env)
    createStaticLibBuilder(env)

    WDK.MergeShellEnv(env)

    env.SetDefault(STATIC_AND_SHARED_OBJECTS_ARE_THE_SAME=1)

    env.Append(DDKDRVEMITTER=[_pdbEmitter])
    env.Append(DDKSHLIBEMITTER=[_dllEmitter])
    env['_PDB'] = parts.tools.mslink.pdbGenerator
    env.SetDefault(DDKCCPDBFLAGS=SCons.Util.CLVar(['${"/Z7" if PDB else ""}']))
    env.SetDefault(DDKCCPCHFLAGS=SCons.Util.CLVar(['${(PCH and "/Yu%s /Fp%s"%(PCHSTOP or "",File(PCH))) or ""}']))

    env.SetDefault(DDK_MIN_WIN='wnet')

    env.SetDefault(DDKOBJSUFFIX='.dobj')

    env['_ddkplatform'] = _ddkplatform
    env['_ddklibplatform'] = _ddklibplatform
    env['_resolve_wdk_flags'] = _resolve_wdk_flags

    env['DDKDIR'] = r'${WDK.DIR}'
    env['DDKHOSTDIR'] = r'${DDKDIR}\bin\x86'
    env['DDKTARGETARCH'] = r'${_ddkplatform(TARGET_ARCH)}'
    env.SetDefault(DDKHOSTTARGETDIR=r'${DDKHOSTDIR}\${DDKTARGETARCH}')

    env.SetDefault(DDKCC=parts.tools.Common.toolvar(env.Detect(
        [r'${DDKHOSTDIR}\cl.exe', r'${DDKHOSTTARGETDIR}\cl.exe']), ('cl',), env=env))
    env.SetDefault(DDKLINK=parts.tools.Common.toolvar(env.Detect(
        [r'${DDKHOSTDIR}\link.exe', r'${DDKHOSTTARGETDIR}\link.exe']), ('link',), env=env))
    env.SetDefault(DDKAS=parts.tools.Common.toolvar(env.Detect([r'${DDKHOSTDIR}\ml.exe', r'${DDKHOSTTARGETDIR}\ml.exe']) if env['TARGET_ARCH'] == 'x86'
                                                    else env.Detect([r'${DDKHOSTTARGETDIR}\ml64.exe']), ('ml', 'ml64'), env=env))

    env.SetDefault(LIBS=[])
    env.SetDefault(DDKLIBS=[])
    env.SetDefault(DDKSHLIBS=[])
    env.SetDefault(LIBPATH=[])
    env.SetDefault(DDKLIBPATH=[])
    env.SetDefault(CPPPATH=[])
    env.SetDefault(DDKCPPPATH=[])
    env.SetDefault(CPPDEFINES=[])
    env.SetDefault(DDKCPPDEFINES=[])

    env['_DDKLIBFLAGS'] = '${_concat(DDKLIBLINKPREFIX, DDKLIBS+LIBS, DDKLIBLINKSUFFIX, __env__)}'
    env['_DDKSHLIBFLAGS'] = '${_concat(DDKLIBLINKPREFIX, DDKSHLIBS+LIBS, DDKLIBLINKSUFFIX, __env__)}'
    env['_DDKLIBDIRFLAGS'] = '$( ${_concat(DDKLIBDIRPREFIX, DDKLIBPATH+LIBPATH, DDKLIBDIRSUFFIX, __env__, RDirs, TARGET, SOURCE)} $)'
    env['_DDKCPPINCFLAGS'] = '$( ${_concat(DDKINCPREFIX, DDKCPPPATH+CPPPATH, DDKINCSUFFIX, __env__, RDirs, TARGET, SOURCE)} $)'
    env['_DDKCPPDEFFLAGS'] = '${_defines(DDKCPPDEFPREFIX, DDKCPPDEFINES+CPPDEFINES, DDKCPPDEFSUFFIX, __env__)}'

    env['_DDKCPPDEFINES'] = '${_defines(DDKCPPDEFPREFIX, _resolve_wdk_flags(__env__, "_ddkcppdefines"), DDKCPPDEFSUFFIX, __env__)}'
    env['_DDKLIBPATH'] = '$( ${_concat(DDKLIBDIRPREFIX, _resolve_wdk_flags(__env__, "_ddklibpath"), DDKLIBDIRSUFFIX, __env__, RDirs, TARGET, SOURCE)} $)'
    env['_DDKLINKFLAGS'] = '${_resolve_wdk_flags(__env__, "_ddklinkflags")}'
    env['_DDKSHLINKFLAGS'] = '${_resolve_wdk_flags(__env__, "_ddkshlinkflags")}'
    env['_DDKLIBS'] = '${_concat(DDKLIBLINKPREFIX, _resolve_wdk_flags(__env__, "_ddklibs"), DDKLIBLINKSUFFIX, __env__)}'

    env['_DDKCCCOMCOM'] = '$DDKCPPFLAGS $_DDKCPPDEFFLAGS $_DDKCPPDEFINES $_DDKCPPINCFLAGS $DDKCCPCHFLAGS $DDKCCPDBFLAGS'

    env.SetDefault(DDKLIBLINKPREFIX='')
    env.SetDefault(DDKLIBLINKSUFFIX='.lib')
    env.SetDefault(DDKLIBDIRPREFIX='-LIBPATH:')
    env.SetDefault(DDKLIBDIRSUFFIX='')
    env.SetDefault(DDKLIBPREFIXES=['$DDKLIBLINKPREFIX'])
    env.SetDefault(DDKLIBSUFFIXES=['$DDKLIBLINKSUFFIX'])
    env.SetDefault(DDKINCPREFIX='-I')
    env.SetDefault(DDKINCSUFFIX='')

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

    env['DDKCCCOM'] = '${TEMPFILE("$DDKCC -Fo$TARGET -c $SOURCES $DDKCFLAGS $DDKCCFLAGS $_DDKCCCOMCOM")}'
    env['DDKCPPPATH'] = [r'${DDKDIR}\inc\ddk', r'${DDKDIR}\inc\api', r'${DDKDIR}\inc\crt']
    env['DDKLINKCOM'] = SCons.Action.Action(
        '${TEMPFILE("$DDKLINK $_DDKLIBPATH $_DDKLIBDIRFLAGS $_DDKLINKFLAGS $DDKLINKFLAGS /OUT:$TARGET.windows $_DDKLIBDIRFLAGS $_DDKLIBFLAGS $_DDKLIBS $_PDB $SOURCES.windows")}')
    env.SetDefault(DDKLINKFLAGS=[])
    env['DDKASCOM'] = '${TEMPFILE("$DDKAS $DDKASFLAGS $_DDKCPPDEFFLAGS $_DDKCPPDEFINES $_DDKCPPINCFLAGS -c -Fo$TARGET $SOURCES")}'

    env.SetDefault(DDKCFLAGS='-nologo')

    env['DDKCXXCOM'] = '${TEMPFILE("$DDKCXX -Fo$TARGET -c $SOURCES $DDKCXXFLAGS $DDKCCFLAGS $_DDKCCCOMCOM")}'
    env.SetDefault(DDKCPPDEFPREFIX='-D')
    env.SetDefault(DDKCPPDEFSUFFIX='')
    env.SetDefault(DDKDRVSUFFIX='.sys')

    # Static libraries
    env.SetDefault(DDKARFLAGS=SCons.Util.CLVar('-nologo'))
    env['DDKARCOM'] = '$DDKLINK ${TEMPFILE("-lib $DDKARFLAGS -OUT:$TARGET $SOURCES")}'

    # Shared libraries
    env.SetDefault(DDKSHLIBPREFIX='')
    env.SetDefault(DDKSHLIBSUFFIX='.dll')
    env['DDKSHLINKCOM'] = SCons.Action.Action(
        '${TEMPFILE("$DDKLINK -dll $_DDKSHLINKFLAGS $DDKSHLINKFLAGS /OUT:$TARGET.windows $_DDKLIBPATH $_DDKLIBDIRFLAGS $_DDKSHLIBFLAGS $_PDB $SOURCES.windows")}')
    env.SetDefault(DDKSHLINKFLAGS=[])


def exists(env):
    return WDK.Exists(env)
