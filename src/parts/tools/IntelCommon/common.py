

from parts.tools.Common.ToolInfo import ToolInfo
from parts.tools.Common.ToolSetting import ToolSetting
from parts.version import version_range

intel_9 = r'(9)([0-1])'
intel_9_posix = r'(9).(\d).(\d\d\d)'
intel_10 = r'(10)(\d).(\d\d\d)'
intel_10_posix = r'(10).(\d).(\d\d\d)'
intel_11 = r'(11)(\d).(\d\d\d)'
intel_11_outer = r'(11).(\d)'
intel_11_inner = r'(\d\d\d)'
intel_12_posix = r'composerxe-(2011)\.(\d+.\d+)'
intel_12_1_posix = r'composer_xe_(2011)_sp1\.(\d+.\d+)'

# hopefully a stable base
intel_13_plus_posix = r'composer_xe_(20\d\d(_sp\d+)?)\.(\d+.\d+)'
intel_19_plus_posix = r'compilers_and_libraries_(\d+.\d+.\d+)'

# different layout in registry
intel_11_1 = r'\d\d\d'


def MatchVersionNumbers(verStr1, verStr2):

    major1, minor1, rev1, junk = (verStr1 + '.-1.-1.-1').split('.', 3)
    major1 = int(major1)
    minor1 = int(minor1)
    rev1 = int(rev1)

    major2, minor2, rev2, junk = (verStr2 + '.-1.-1.-1').split('.', 3)
    major2 = int(major2)
    minor2 = int(minor2)
    rev2 = int(rev2)

    if major1 != major2:
        return False
    if major1 == major2 and (minor1 == -1 or minor2 == -1):
        return True
    if minor1 != minor2:
        return False
    if minor1 == minor2 and (rev1 == -1 or rev2 == -1):
        return True
    if rev1 == rev2:
        return True

    return False


class IntelcInfo(ToolInfo):

    def __init__(self, version, install_scanner, script, subst_vars, shell_vars, test_file):
        ToolInfo.__init__(self, version, install_scanner, script, subst_vars, shell_vars, test_file)
        self.version = version_range(version)

    def version_set(self):
        return self.version

    def resolve_version(self, version):
        return self.install_root.resolve_version(version)


Intelc = ToolSetting('INTELC')
