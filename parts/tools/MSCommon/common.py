import os
import SCons.Util
from parts.tools.Common.ToolSetting import ToolSetting
import parts.platform_info

logfile = os.environ.get('SCONS_MSCOMMON_DEBUG')
if logfile:
    try:
        import logging
    except ImportError:
        def debug(x): return open(logfile, 'a').write(x + '\n')
    else:
        logging.basicConfig(filename=logfile, level=logging.DEBUG)
        debug = logging.debug
else:
    def debug(x): return None


def is_win64():
    """Return true if running on windows 64-bits OS."""
    return parts.platform_info.OSBit() == 64


def read_reg(value):
    return SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE, value)[0]


def get_current_sdk():
    ''' get SDK path based on reg key used for vc 9.0 and 10'''
    # note this key is used for both 32-bit and 64-bit systems
    # this mean the that default path will always be program file/xxx
    # even on 64-bit systems
    key = 'SOFTWARE\Microsoft\Microsoft SDKs\Windows\CurrentInstallFolder'
    dir = ''
    try:
        dir = SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE, key)[0]
        debug('Found SDK dir in registry: %s' % dir)
    except WindowsError as e:
        debug('Did not find SDK dir key %s in registry' %
              (key))
    return dir


def get_current_sdk11():
    ''' get SDK path based on reg key used for vc 11'''
    # note this key is used for both 32-bit and 64-bit systems
    # this mean the that default path will always be program file/xxx
    # even on 64-bit systems
    key = 'SOFTWARE\Microsoft\Microsoft SDKs\Windows\v8.0\CurrentInstallFolder'
    dir = ''
    try:
        dir = SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE, key)[0]
        debug('Found SDK dir in registry: %s' % dir)
    except WindowsError as e:
        debug('Did not find SDK dir key %s in registry' %
              (key))
    return dir


def framework_root():
    VS_HKEY_BASE = "\\"
    comps = ''
    if is_win64():
        VS_HKEY_BASE = "\\Wow6432Node\\"
    key = 'Software%sMicrosoft\\.NETFramework\\InstallRoot' % (VS_HKEY_BASE)
    try:
        comps = read_reg(key)
        debug('Found framework dir in registry: %s' % comps)
    except WindowsError as e:
        debug('Did not find framework dir key %s in registry' %
              (key))
        return ''
    return comps


def framework_root64():
    ''' currently this value when added seem to be messed up in the scripts
    on 32-bit OS systems. Since this path is always bad, we don't add it in these
    cases'''
    comps = ''
    key = 'Software\\Microsoft\\.NETFramework\\InstallRoot'
    try:
        comps = read_reg(key)
        if comps[-3:] != '64\\':
            comps = comps[:-1] + '64\\'
            if os.path.exists(comps) == False:
                debug('Did not find framework64 dir')
                return ''
        debug('Found framework64 dir in registry: %s' % comps)
    except WindowsError as e:
        debug('Did not find framework64 dir key %s in registry' %
              (key))
        return ''
    return comps


def validate_vars(env):
    """Validate the PCH and PCHSTOP construction variables."""
    if 'PCH' in env and env['PCH']:
        if 'PCHSTOP' not in env:
            raise SCons.Errors.UserError("The PCHSTOP construction must be defined if PCH is defined.")
        if not SCons.Util.is_String(env['PCHSTOP']):
            raise SCons.Errors.UserError("The PCHSTOP construction variable must be a string: %r" % env['PCHSTOP'])


# VC teh compiler and related tools
msvc = ToolSetting('MSVC')
# Microsft SDK (Platform)
mssdk = ToolSetting('MSSDK')
# Microsoft VS integration SDK (VSIP)
vssdk = ToolSetting('VSSDK')
