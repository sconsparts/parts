from __future__ import absolute_import, division, print_function

from parts.config import *


def map_default_version(env):
    return env['WDK_VERSION']


config = configuration(map_default_version)

_ddkcppdefines = {
    'wxp': ['_WIN32_WINNT=0x0501', 'WINVER=0x0501', '_WIN32_IE=0x0603', 'NTDDI_VERSION=0x05010200'],
    'wnet': ['_WIN32_WINNT=0x0502', 'WINVER=0x0502', '_WIN32_IE=0x0603', 'NTDDI_VERSION=0x05020100'],
    'wlh': ['_WIN32_WINNT=0x0600', 'WINVER=0x0600', '_WIN32_IE=0x0700', 'NTDDI_VERSION=0x06000100'],
    'win7': ['_WIN32_WINNT=0x0601', 'WINVER=0x0601', '_WIN32_IE=0x0800', 'NTDDI_VERSION=0x06010000']
}

_ddklibpath = {
    'wxp': [r'${DDKDIR}\lib\wxp\i386'],
    'wnet': [r'${DDKDIR}\lib\wnet\i386'],
    'wlh': [r'${DDKDIR}\lib\wlh\i386'],
    'win7': [r'${DDKDIR}\lib\win7\i386']
}

_ddklinkcommon = [
    '-STACK:0x40000,0x1000', '-driver', '-base:0x10000',
    '-functionpadmin:5', '-safeseh', '-entry:GsDriverEntry@8'
]

_ddklinkflags = {
    'wxp': _ddklinkcommon + ['/align:0x80', r'/stub:${DDKDIR}\lib\wxp\stub512.com', '/subsystem:native,5.01'],
    'wnet': _ddklinkcommon + ['/subsystem:native,5.02', r'${DDKDIR}\lib\wnet\i386\hotpatch.obj'],
    'wlh': _ddklinkcommon + ['/subsystem:native,6.00', r'${DDKDIR}\lib\wlh\i386\hotpatch.obj'],
    'win7': _ddklinkcommon + ['/subsystem:native,6.01', r'${DDKDIR}\lib\win7\i386\hotpatch.obj']
}

_ddkshlinkcommonflags = [
    '-safeseh'
]

_ddkshlinkflags = {
    'wxp': _ddkshlinkcommonflags + ['/align:0x80', r'/stub:${DDKDIR}\lib\wxp\stub512.com', '/subsystem:native,5.01'],
    'wnet': _ddkshlinkcommonflags + ['/subsystem:native,5.02', r'${DDKDIR}\lib\wnet\i386\hotpatch.obj'],
    'wlh': _ddkshlinkcommonflags + ['/subsystem:native,6.00', r'${DDKDIR}\lib\wlh\i386\hotpatch.obj'],
    'win7': _ddkshlinkcommonflags + ['/subsystem:native,6.01', r'${DDKDIR}\lib\win7\i386\hotpatch.obj']
}

_ddklibs = {
    'wxp': ['sehupd'],
    'wnet': ['sehupd'],
    'wlh': [],
    'win7': [],
}

config.VersionRange("7600.16385.0-7600.16385.2",
                    replace=ConfigValues(
                        _ddkcppdefines=_ddkcppdefines,
                        _ddklibpath=_ddklibpath,
                        _ddklinkflags=_ddklinkflags,
                        _ddkshlinkflags=_ddkshlinkflags,
                        _ddklibs=_ddklibs,
                    ),
                    append=ConfigValues(
                        DDKCCFLAGS=['-FC', '-GS', '-EHs-c-', '-Zc:wchar_t-', '-Zl',
                                    '-Zp8', '-Gy', '-Gm-', '-cbstring', '-W3',
                                    '-EHs-c-', '-GR-', '-GF', '-GS', '-Z7', '-Oxs',
                                    '-Z7', '-DKMDF_MAJOR_VERSION_STRING=01', '-DKMDF_MINOR_VERSION_STRING=009',
                                    '-wd4603', '-wd4627', '-typedil-', r'-FI${DDKDIR}\inc\api\warning.h',
                                    '-Gz', '-hotpatch', '-Oy'
                                    ],
                        DDKCPPDEFINES=['WIN32=100', '_X86_=1', 'i386=1',
                                       'CONDITION_HANDLING=1', 'NT_UP=1', 'NT_INST=0', '_NT1X_=100',
                                       'WINNT=1',
                                       'WIN32_LEAN_AND_MEAN=1', 'DEVL=1', 'DBG=1', '__BUILDMACHINE__=WinDDK',
                                       'FPO=0', '_DLL=1', 'NDEBUG', 'DEPRECATE_DDK_FUNCTIONS=1',
                                       'MSC_NOOPT',
                                       '_X86_=1', 'i386=1', 'STD_CALL'
                                       ],
                        DDKLIBPATH=[],
                        DDKLIBS=[r'ntoskrnl', 'hal', 'wmilib', 'BufferOverflowK'],
                        DDKSHLIBS=['ntoskrnl', 'hal', 'wmilib', 'BufferOverflow', 'ntstrsafe', 'ntdll'],
                        DDKLINKFLAGS=[
                            '-MERGE:_PAGE=PAGE', '-MERGE:_TEXT=.text', '-SECTION:INIT,d',
                            '-OPT:REF', '-OPT:ICF', '-IGNORE:4198,4010,4037,4039,4065,4070,4078,4087,4089,4221',
                            '-INCREMENTAL:NO', '-release', '-NODEFAULTLIB', '-WX', '-debug', '-debugtype:cv,fixup,pdata',
                            '-version:6.1', '-osversion:6.1', '-pdbcompress',
                        ],
                        DDKASFLAGS=[
                            '-nologo', '-Cx', '-Zi',
                            '-safeseh', '-Zm', '-coff',
                        ],
                    )
                    )
