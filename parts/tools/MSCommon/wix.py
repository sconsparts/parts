"""
The file contains WiX tool stuff which we want to be in single instance.
This file is not loaded by SCons.Tool() call it is called with Python
import technique so its uniqueness is supported by python.
"""
import os
import re
import SCons.Scanner
import SCons.Builder
import SCons.Tool
import SCons.Node.FS
import SCons.Util
import xml
import xml.sax
from xml.dom.pulldom import PullDOM
from parts.platform_info import SystemPlatform
from parts.tools.Common.ToolSetting import ToolSetting
from parts.tools.Common.ToolInfo import ToolInfo
from parts.tools.Common.Finders import PathFinder
from parts.tools.Common.Finders import EnvFinder
from parts.tools.MSCommon.MsiFinder import MsiFinder
from parts import api

wix = ToolSetting('WIX')

wix.Register(
    hosts = [SystemPlatform('win32', 'any')],
    targets = [SystemPlatform('win32', 'any')],
    info = [
        ToolInfo(
            version='3.5',
            install_scanner=[
                MsiFinder(
                    r'Windows Installer XML.*',
                    r'CandleBinaries'
                    ),
                PathFinder([
                    r'c:\Program Files (x86)\Windows Installer XML v3.5\bin'
                ]),
                EnvFinder([
                    'WIX_PATH'
                ], '.')
            ],
            script=False,
            subst_vars={},
            shell_vars={
                'PATH': '${WIX.INSTALL_ROOT}'
                },
            test_file='candle.exe'
            ),
        ToolInfo(
            version='3.6',
            install_scanner=[
                MsiFinder(
                    r'WiX Toolset v3\.6 Core.*',
                    r'candle.exe'
                    ),
                PathFinder([
                    r'C:\Program Files (x86)\WiX Toolset v3.6\bin'
                ]),
                EnvFinder([
                    'WIX_PATH'
                ], '.')
            ],
            script=False,
            subst_vars={},
            shell_vars={
                'PATH': '${WIX.INSTALL_ROOT}'
                },
            test_file='candle.exe'
            ),
        ToolInfo(
            version='3.7',
            install_scanner=[
                MsiFinder(
                    r'WiX Toolset v3\.7 Core.*',
                    r'candle.exe'
                    ),
                PathFinder([
                    r'C:\Program Files (x86)\WiX Toolset v3.7\bin'
                ]),
                EnvFinder([
                    'WIX_PATH'
                ], '.')
            ],
            script=False,
            subst_vars={},
            shell_vars={
                'PATH': '${WIX.INSTALL_ROOT}'
                },
            test_file='candle.exe'
            ),
        ToolInfo(
            version='3.8',
            install_scanner=[
                MsiFinder(
                    r'WiX Toolset v3\.8 Core.*',
                    r'candle.exe'
                    ),
                PathFinder([
                    r'C:\Program Files (x86)\WiX Toolset v3.8\bin'
                ]),
                EnvFinder([
                    'WIX_PATH'
                ], '.')
            ],
            script=False,
            subst_vars={},
            shell_vars={
                'PATH': '${WIX.INSTALL_ROOT}'
                },
            test_file='candle.exe'
            ),
        ToolInfo(
            version='3.9',
            install_scanner=[
                MsiFinder(
                    r'WiX Toolset v3\.9 Core.*',
                    r'candle.exe'
                    ),
                PathFinder([
                    r'C:\Program Files (x86)\WiX Toolset v3.9\bin'
                ]),
                EnvFinder([
                    'WIX_PATH'
                ], '.')
            ],
            script=False,
            subst_vars={},
            shell_vars={
                'PATH': '${WIX.INSTALL_ROOT}'
                },
            test_file='candle.exe'
            ),
        ToolInfo(
            version='3.10',
            install_scanner=[
                MsiFinder(
                    r'WiX Toolset v3\.10 Core.*',
                    r'candle.exe'
                    ),
                PathFinder([
                    r'C:\Program Files (x86)\WiX Toolset v3.10\bin'
                ]),
                EnvFinder([
                    'WIX_PATH'
                ], '.')
            ],
            script=False,
            subst_vars={},
            shell_vars={
                'PATH': '${WIX.INSTALL_ROOT}'
                },
            test_file='candle.exe'
            )
        ]

    )

class WixPreprocessor(object):
    '''
    This is a helper class used by WiX tool source scanners to emulate
    candle.exe pre-processor.
    '''
    class SysVars(object):
        '''
        This is a class to emulate $(sys.VARNAME) WiX preprocossor variables.
        VARNAME can be one of the following: PLATFORM, SOURCEFILEPATH, SOURCEFILEDIR,
        CURRENTDIR. See WiX docs for more information.
        '''
        __slots__ = ['cwd', 'PLATFORM', 'source']

        def __init__(self, cwd, source, platform):
            self.cwd = cwd
            self.source = source
            self.PLATFORM = platform

        @property
        def SOURCEFILEPATH(self):
            return self.source.abspath

        @property
        def SOURCEFILEDIR(self):
            return self.source.dir.abspath + '\\'

        @property
        def CURRENTDIR(self):
            return self.cwd.abspath + '\\'

    class EnvVars(object):
        '''
        This class emulates $(env.VARNAME) WiX preprocessor variables.
        See WiX docs for more information.
        '''
        __slots__ = ['ENV']
        def __init__(self, ENV):
            self.ENV = dict(ENV)

        def __getattr__(self, name):
            try:
                return str(object.__getattribute__(self, 'ENV')[name])
            except KeyError:
                return ''

    class VarVars(object):
        '''
        This class emulates $(var.VARNAME) WiX preprocossor variables.
        '''
        def __init__(self, vars):
            for var in vars:
                defs = re.match('^(?P<name>[^=]+)=(?P<value>.*)$', var)
                if defs:
                    self.__dict__[defs.groupdict()['name']] = defs.groupdict()['value']


    def __init__(self, env, source, pp_var_name=None, include_path=None, path=None):
        self.__env = env
        """__env is SCons.Script.Environment instance"""
        self.__lvars = {
            'var': self.VarVars(SCons.Util.flatten(pp_var_name and self.__env.get(pp_var_name) or [])),
            'env': self.EnvVars(self.__env['ENV']),
            'sys': self.SysVars(self.__env.Dir('.'), source, 'Intel')
        }
        '''__lvars is a dict object to store different kinds of WiX preprocessor variables.'''
        self.__sources = []
        '''__sources serves as stack of source file Node objects.'''
        self.__include_path = include_path or ()
        '''List of paths to look for *.wxi files'''
        self.__path = path or ()
        '''List of paths to look for File and Merge WiX node files'''

    def define(self, data):
        '''
        This function is called by XML parser content handler when it faces <?define [expression]?> directive.
        @param data: is a raw expression. The function parses it and puts its value to $(var.VARNAME)
        WiX preprocessor variable.
        '''
        gd = re.match(r'(?P<name>[^=\s]+)(\s*=\s*(?P<value>\S+)?)?', data.strip()).groupdict()
        name = gd['name']; value = gd['value']
        if value is not None:
            if re.match(r'^([\'"]).*\1$', value):
                value = value[1:-1]
        else:
            value = 1
        setattr(self.__lvars['var'], name, value)

    def include(self, name):
        '''
        This is called by XML parser content handler when it faces <?include path/to/file ?> directive.
        @param data: expression to be converted into wxi file name.

        Since the raw name may include some preprocessor expression this function expands the name
        into a plain string. Then it tries to find the file Node on a file system via call to
        env.FindFile function.
        If the file is found the function stores current source file being processed in a stack
        and sets the found file as the source and returns the file Node.

        If the file is not found the function returns None.

        Every successfull call to the include function must be followed by call to leave function.
        '''

        # Strip and unquote the name
        name = re.match(r'^([\'"])?(.*)(?(1)\1)$', name.strip()).group(2)
        cursource = self.__lvars['sys'].source
        name = self.expand(name)
        result = self.__env.FindFile(name, (cursource.dir,) + self.__include_path)
        if result:
            self.__sources.append(self.__lvars['sys'].source)
            self.__lvars['sys'].source = result
        return result

    def leave(self):
        '''
        Notifies the preprocessor that it finished with included wxi file and returned to
        previous source in the stack.
        '''
        if self.__sources:
            self.__lvars['sys'].source = self.__sources.pop()

    def file(self, name):
        '''
        Tries to find a file with the specified name. Returns SCons.Node.FS.Base node on success
        and None on failure.
        '''
        return self.__env.FindFile(self.expand(name), (self.__env.Dir('.'),) + self.__path)

    def expand(self, strsubst):
        '''
        Expands a string with WiX preprocessor macros into a real one
        '''
        def replace(match):
            '''
            This function is called for each WiX preprocessor macro found in string being expanded.
            '''
            matchdict = match.groupdict()
            # Expand replacement because it can also include some WiX preprocessor expressions.
            try:
                return self.expand(getattr(self._WixPreprocessor__lvars[matchdict['var']], matchdict['name']))
            except AttributeError:
                return ''
        return re.sub(r'\$\((?P<var>var|sys|env)\.(?P<name>[^)]+)\)', replace, strsubst)

class WixIncludeHandler(PullDOM):
    '''
    We use pull model xml parser to go through the wxs file tag by tag.
    '''
    def __init__(self, preprocessor, on_source = lambda file_node: None, on_include = lambda file_node: None):
        PullDOM.__init__(self, None)
        self.preprocessor = preprocessor
        self.on_source = on_source
        self.on_include = on_include

    def processingInstruction(self, target, data):
        '''
        This function is called by xml parser when it gets xml pre-processor
        directive.
        '''
        if target == 'include':
            source = self.preprocessor.include(data)
            if source:
                self.on_include(source)
                if source.exists():
                    # go through it because it can have files specified in it
                    parser = xml.sax.make_parser()
                    parser.setContentHandler(self.__class__(
                        self.preprocessor, self.on_source, self.on_include))
                    parser.parse(source.abspath)
                self.preprocessor.leave()
        elif target == 'define':
            self.preprocessor.define(data)
        else:
            PullDOM.processingInstruction(self, target, data)

class WixSourceHandler(WixIncludeHandler):
    def __init__(self, preprocessor, on_source = lambda file_node: None, on_include = lambda file_node: None):
        WixIncludeHandler.__init__(self, preprocessor, on_source, on_include)
        self.__path = []
        '''Contains list of tuples of form (path element string, is it a root)'''

    @property
    def path(self):
        '''
        returns list of strings representing elements of the path to a directory
        where to look for File and Merge nodes.
        '''
        result = []
        for name, root in reversed(self.__path):
            result.append(name)
            if root:
                break
        result.reverse()
        return result

    '''Every WiX Element of one of the following types may have SourceFile attribute.
    Our scanners use the attribute to find dependencies.

    TODO: generate the list dynamically from ${WIX.INSTALL_ROOT}/bin/wix.xsd file.
    '''
    nodes_with_SourceFile = set(['Catalog', 'BootstrapperApplication', 'UX', 'Payload',
        'UpgradeImage', 'TargetImage', 'DigitalCertificate', 'DigitalSignature',
        'SFPCatalog', 'Merge', 'Binary', 'Icon', 'EmbeddedUI', 'EmbeddedUIResource'])

    def startElement(self, tag, attrs):
        WixIncludeHandler.startElement(self, tag, attrs)
        if tag in self.nodes_with_SourceFile:
            if 'SourceFile' in attrs.getNames():
                name = attrs.getValue('SourceFile')
            else:
                name = os.sep.join(self.path + [attrs.getValue('Id')])
            file = self.preprocessor.file(name)
            if file:
                self.on_source(file)
        elif tag == 'File':
            if 'Source' in attrs.getNames():
                name = attrs.getValue('Source')
            else:
                if 'Name' in attrs.getNames():
                    name = attrs.getValue('Name')
                else:
                    name = attrs.getValue('Id')
                name = os.sep.join(self.path + [name])
            file = self.preprocessor.file(name)
            if file:
                self.on_source(file)
        elif tag == 'Directory':
            if 'FileSource' in attrs.getNames():
                name = attrs.getValue('FileSource')
                root = True
            else:
                root = not self.__path
                if 'SourceName' in attrs.getNames():
                    name = attrs.getValue('SourceName')
                elif 'Name' in attrs.getNames():
                    name = attrs.getValue('Name')
                else:
                    name = attrs.getValue('Id')
            self.__path.append((name, root))

    def endElement(self, tag):
        if tag == 'Directory':
            if self.__path:
                self.__path.pop()
        WixIncludeHandler.endElement(self, tag)

def wixSrcScanner(node, env, path):
    """
    Returns list of files changes in those leads to changes in .wixobj's content.
    """
    if not node.exists() and not node.rexists():
        return []
    preprocessor = WixPreprocessor(env, node, 'WIXPPDEFINES', include_path=path)

    result = []
    parser = xml.sax.make_parser()
    parser.setContentHandler(WixIncludeHandler(preprocessor, on_include = result.append))
    try:
        parser.parse(node.rfile().abspath)
    except xml.sax.SAXParseException:
        pass
    return result

def wixObjScanner(node, env, path):
    """
    This function returns a list of file nodes changes in those
    make the resulting .msi be re-built.
    """
    # The node is .wixobj file. We cannot rely on its content because its format is
    # undocumented and is the subject to change. Instead we get the first node's
    # source which is .wxs and have well documented format.
    if not node.sources or not node.sources[0].rexists():
        return []
    source = node.sources[0].rfile()

    path = (node.dir,) + path

    # Pre-processor path is different from the one we are supplied.
    include_path = SCons.Scanner.FindPathDirs('WIXPPPATH')(
            node.env or env, target=[node], source=[source])

    preprocessor = WixPreprocessor(node.env or env, source, 'WIXPPDEFINES',
            include_path=include_path, path=path)
    result = []

    parser = xml.sax.make_parser()
    parser.setContentHandler(WixSourceHandler(preprocessor, on_source = result.append))
    try:
        parser.parse(source.abspath)
    except xml.sax.SAXParseException:
        pass

    return result

SCons.Tool.SourceFileScanner.add_scanner(
    '.wixobj',
    SCons.Scanner.Scanner(
        wixObjScanner,
        path_function=SCons.Scanner.FindPathDirs('WIXFILEPATH')
    )
)

SCons.Tool.SourceFileScanner.add_scanner(
    '.wxs',
    SCons.Scanner.Scanner(
        wixSrcScanner,
        path_function=SCons.Scanner.FindPathDirs('WIXPPPATH')
    )
)

def wixEnvScanner(varnames):
    '''
    Creates a callable to be used by env scanner.
    @param[in] varnames: sequence of tuples of form (entries_var, prefs_var, suffs_var)
    '''
    def scan(node, env, path = ()):
        '''
        This scanner looks through the env for localization, extensions
        '''
        if callable(path):
            path = path()
        result = []
        for items, prefs, suffs in varnames:
            try:
                exts = env[items]
            except KeyError:
                pass
            else:
                pref, suff = env.get(prefs, ''), env.get(suffs, '')
                for ext in exts:
                    if SCons.Util.is_String(ext):
                        ext = env.subst(ext)
                        ext = SCons.Util.adjustixes(ext, pref, suff)
                        ext = SCons.Node.FS.find_file(ext, path)
                        if ext:
                            result.append(ext)
                    else:
                        result.append(ext)

        return result
    return scan

wixObjEnvScanner = SCons.Scanner.Scanner(
    wixEnvScanner([('WIXLINKEXTENSIONS', 'WIXLINKEXTPREFIX', 'WIXLINKEXTSUFFIX'),]),
    path_function = SCons.Scanner.FindPathDirs('WIX_TOOL_PATHS'))

wixMsiEnvScanner = SCons.Scanner.Scanner(
    wixEnvScanner([('WIXLINKEXTENSIONS', 'WIXLINKEXTPREFIX', 'WIXLINKEXTSUFFIX'),
                  ('WIXLOCALIZATION', 'WIXLCLPREFIX', 'WIXLCLSUFFIX')]),
    path_function = SCons.Scanner.FindPathDirs('WIX_TOOL_PATHS'))

def createWixObjectBuilder(env):
    """
    The function adds WixObject builder to the environment.
    """
    try:
        result = env['BUILDERS']['WixObject']
    except KeyError:
        result = SCons.Builder.Builder(
                action = '$WIXCLCOM',
                prefix = '$WIXOBJPREFIX',
                suffix = '$WIXOBJSUFFIX',
                src_suffix = '.wxs',
                single_source = 1,
                source_scanner = SCons.Tool.SourceFileScanner,
                target_scanner = wixObjEnvScanner,
                target_factory = SCons.Node.FS.File,
                source_factory = SCons.Node.FS.File
                )
        env['BUILDERS']['WixObject'] = result

    return result

def createMsiBuilder(env):
    """
    Adds MSI builder to the environment.
    """
    try:
        result = env['BUILDERS']['MSI']
    except KeyError:
        result = SCons.Builder.Builder(
                action = '$WIXLINKCOM',
                prefix = '$MSIPREFIX',
                suffix = '$MSISUFFIX',
                src_suffix = '$WIXOBJSUFFIX',
                src_builder = 'WixObject',
                source_scanner = SCons.Tool.SourceFileScanner,
                target_scanner = wixMsiEnvScanner,
                target_factory = SCons.Node.FS.File,
                source_factory = SCons.Node.FS.File
                )
        env['BUILDERS']['MSI'] = result

    return result


# vim: set et ts=4 sw=4 ft=python :

