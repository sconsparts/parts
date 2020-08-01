'''
Contains basic functions needed to provide bitness of OS and architecture
These function provide information on the current running platform.
User should not need these much, but it can be useful. With cross platform support
added some day this will not be needed external, but instead user will use env
var defined to to tell what has been targeted as the build env.
'''


import os
import platform
import re
import subprocess
import sys

import parts.api as api
import parts.common as common
import parts.core as core
import parts.glb as glb
import SCons.Platform
from SCons.Debug import logInstanceCreation


def UpdatePlatformRegEx():

    arch_str = ''
    os_str = ''
    for arch in glb.valid_arch:
        if arch_str == '':
            arch_str = arch_str + arch
        else:
            arch_str = arch_str + '|' + arch

    for os in glb.valid_os:
        if os_str == '':
            os_str = os_str + os
        else:
            os_str = os_str + '|' + os

    glb.valid_platform_re = re.compile('(?P<os>' + os_str + ')?(?P<sep1>-)?(?P<arch>' + arch_str + ')?$', re.IGNORECASE)


def UpdateValidArchList():
    for k, v in glb.arch_map.items():
        if k not in glb.valid_arch:
            glb.valid_arch.append(k)
    glb.valid_arch.sort(key=lambda x: len(x))
    UpdatePlatformRegEx()


def UpdateValidOSList():
    for k, v in glb.os_map.items():
        if k not in glb.valid_os:
            glb.valid_os.append(k)
    glb.valid_os.sort(key=lambda x: len(x))
    UpdatePlatformRegEx()


if glb.valid_arch is None or glb.valid_os is None:
    glb.valid_arch = []
    glb.valid_os = []
    UpdateValidArchList()
    UpdateValidOSList()


def MapArchitecture(val):
    '''
    Maps the value of lowlevel architures to high level one that
    are more generic and useful.

    supported currently
        x86 -- Intel(r) line of compatible 32-bit chips
        x86_64 -- The 64-bit extended memory form of x86 (AMD64 or em64t)
        ia64 --

        # to add other system here
    '''
    return glb.arch_map.get(val, None)


def MapOS(val):
    '''
    Maps the value of lowlevel OS names to high level one that
    are more generic and useful to scons.

    supported currently
        win32 -- Windows OS of all flavors, both 32bit and 64bit
        posix -- All Linux and Unix flavors
        darwin -- All Mac OS flavors
        sunos -- All Solaris flavors

        # to add other system here
    '''
    return glb.os_map.get(val, None)


def ValidatePlatform(platform_str):
    tmp = glb.valid_platform_re.match(platform_str)
    if tmp is not None:
        dict = tmp.groupdict()
        if (not dict.get('os') and not dict.get('arch')) or (
                dict.get('sep1') == '-' and (not dict.get('os') or not dict.get('arch'))):
            return False
        else:
            if dict.get('sep1') == '-':
                tmp = MapOS(dict.get('os')), MapArchitecture(dict.get('arch'))
            elif dict.get('arch'):
                tmp = None, MapArchitecture(dict.get('arch'))
            elif dict.get('os'):
                tmp = MapOS(dict.get('os')), None
            return tmp
    else:
        return False


def OSBit():
    '''
        OSBit

        returns the Scons os bit type
        This is important if you have a 64-bit chip but a 32-bit OS
        in this case you often can't or don't want to compile as a 64-bit
        application.
    '''
    # Unfortunately, python does not provide any way to tell if the OS itself
    # is 32-bit or 64-bit.  What is worse is that 32-bit vs 64-bit python
    # effects
    # the value Python might return.  This tell us nothing of the current
    # system
    # The test below returns
    if sys.platform == 'win32':
        # this test fails on server 2008
        # may fail on window 7 ( don't know yet)
        value = r"Software\Wow6432Node"
        ret = None
        try:
            ret = SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE, value)
        except Exception:
            pass
        if ret is None and os.environ.get('PROCESSOR_ARCHITEW6432', None) is None:
            return 32
        else:
            return 64
    # assume is is correct.  ## test later the getconf LONG_BIT command
    val = platform.architecture()[0]
    if val[-3:] == 'bit':
        val = val[:-3]
    return int(val)


def ChipArchitecture():
    '''
        ChipArchitecture

        returns the chip archecture
        Returns High level value for the archecture being used
        which is often more useful. Knowing if you have a
        ia32, x64, ia64 in general is more intertesting
        than know if it is an P3 or P4

    '''
    # if win32
    import sys
    if sys.platform == 'win32':
        import os
        val = os.environ.get('PROCESSOR_ARCHITEW6432', '')
        if val == '':
            val = os.environ['PROCESSOR_ARCHITECTURE']
        return MapArchitecture(val)
    elif sys.platform.startswith("sunos") and platform.machine() == 'i86pc':
        pipe = subprocess.Popen(['isainfo', '-k'], stdout=subprocess.PIPE)
        pipe.wait()
        if pipe.stdout.readline().decode().startswith('i386'):
            return MapArchitecture('i386')
        else:
            return MapArchitecture('x86_64')
    elif sys.platform.startswith("darwin"):
        # more reliable way to get interpreter bitness on OS with universl
        # binaries
        is_64bits = sys.maxsize > 2 ** 32
        return MapArchitecture('x86_64' if is_64bits else 'i386')
    # else we just assume the python code will work at this time
    else:
        return MapArchitecture(platform.machine())


class SystemPlatform(common.bindable):

    def __init__(self, os=None, arch=ChipArchitecture()):
        if __debug__:
            logInstanceCreation(self)
        if not os:
            if 'freebsd' in sys.platform.lower():
                os = 'freebsd'
            else:
                os = SCons.Platform.platform_default()

        if arch == ChipArchitecture():
            platform_str = os
        else:
            platform_str = os + '-' + arch
        lst = ValidatePlatform(str(platform_str))
        # if not lst:
        #lst = ValidatePlatform(os)
        if not lst:
            api.output.error_msg(" " + platform_str + " is not a valid target_system value\n")

        if lst[0] is not None:
            os = lst[0]
        if lst[1] is not None:
            arch = lst[1]
        self.key = "_parts_"
        self._env = {
            self.key + "_OS": os,
            self.key + "_ARCH": arch
        }

    @property
    def OS(self):
        return self._env[self.key + "_OS"]

    @OS.setter
    def OS(self, x):
        self._env[self.key + "_OS"] = x

    @property
    def ARCH(self):
        return self._env[self.key + "_ARCH"]

    @ARCH.setter
    def ARCH(self, x):
        self._env[self.key + "_ARCH"] = x

    def _bind(self, env, key):
        # this is a bit of a hack to forward stuff in SCons as it should be in
        # 1.3
        if key == "TARGET_PLATFORM" or key == "HOST_PLATFORM":
            tkey = key.rsplit("_PLATFORM", 1)[0]

            env[tkey + "_ARCH"] = self.ARCH if self.ARCH != 'any' and self.ARCH else env[tkey +
                                                                                         "_ARCH"] if tkey + "_ARCH" in env else ChipArchitecture()  # getArch
            env[tkey + "_OS"] = self.OS if self.OS != 'any' and self.OS else env[tkey +
                                                                                 "_OS"] if tkey + "_OS" in env else SCons.Platform.platform_default()  # getPlatform

            self.key = tkey
            self._env = env

    def _rebind(self, env, key):

        # only want to do this for Target as host in "inmutable"
        # this allows us to clone TARGET_ARCH or TARGET_OS correctly
        # we DON"T want HOST to be changed, it should be inmutable.
        if key == "TARGET_PLATFORM":
            tmp = SystemPlatform(os=env["TARGET_OS"] if "TARGET_OS" in env else self.OS,
                                 arch=env["TARGET_ARCH"] if "TARGET_ARCH" in env else self.ARCH)
        else:
            tmp = SystemPlatform(os=self.OS, arch=self.ARCH)
        tmp._bind(env, key)
        return tmp

    def __eq__(self, rhs):
        if core.util.isString(rhs):
            rhs = target_convert(rhs, base=self)

        return (self.OS == rhs.OS or
                'any' == rhs.OS or
                'any' == self.OS) and \
            (self.ARCH == rhs.ARCH or
                'any' == rhs.ARCH or
                'any' == self.ARCH)

    def __ne__(self, rhs):
        return (not self.__eq__(rhs))

    def __str__(self):
        return self.OS + "-" + self.ARCH

    __repr__ = __str__

    def __hash__(self):
        return hash(str(self))

    def _is_native(self):
        return 'any' != self.OS and 'any' != self.ARCH

    # because of the mapping to ENV we have to do our own copy
    def __copy__(self):
        return SystemPlatform(self.OS, self.ARCH)

    def __deepcopy__(self, memo=None):
        return SystemPlatform(self.OS, self.ARCH)

    def __getitem__(self, key):
        return self.__class__.__dict__[key.upper()].fget(self)

    def __setitem__(self, key, val):
        if (key.upper() in self.__class__.__dict__) == False:
            raise KeyError('SystemPlatform has no member ' + key.upper())
        self.__class__.__dict__[key.upper()].fset(self, val)


if glb._host_platform is None:
    glb._host_platform = SystemPlatform()


def HostSystem():
    return glb._host_platform


def target_convert(str_val, raw_val=None, base=None, error=True):
    host_sys = base is None and glb._host_platform or base
    lst = ValidatePlatform(str_val)
    if not lst:
        if error:
            api.output.error_msg(" " + str_val + " is not a valid target_system value\n")
        return None
    else:
        p = lst[0]
        a = lst[1]
        if p is None:
            p = host_sys.OS
        if a is None:
            a = host_sys.ARCH
        ret = SystemPlatform(p, a)
    return ret


# add configuartion varaible
#api.register.add_variable('OSBITNESS',str(OSBit()),'to be removed??')
api.register.add_variable(['TARGET_PLATFORM', 'target_platform', 'target'],
                          SystemPlatform(glb._host_platform.OS, glb._host_platform.ARCH),
                          'Value of what to type of system to target build for, used to control cross builds',
                          converter=target_convert)

api.register.add_global_parts_object('ChipArchitecture', ChipArchitecture)  # obsolete
api.register.add_global_parts_object('OSBit', OSBit)  # obsolete
# api.register.add_global_parts_object('Host_Platform',HostSystem)
api.register.add_global_object('ChipArchitecture', ChipArchitecture)  # obsolete
api.register.add_global_object('OSBit', OSBit)  # obsolete
api.register.add_global_object('HostPlatform', HostSystem)
api.register.add_global_object('SystemPlatform', SystemPlatform)
# api.register.add_global_object('ValidatePlatform',ValidatePlatform)
