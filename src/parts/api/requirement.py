from __future__ import absolute_import, division, print_function

from .. import common, policy
from ..core import util
from . import output
from ..requirement import (REQ, DefineRequirementSet, requirement,
                           requirement_internal, _added_types)


def AddRequirement(name, requirementname):
    tmp = Requirement(name)
    
    new_req = _added_types.get(requirementname)[0]._values
    if not tmp:
        output.warning_msgf("requirement '{0}' was not found. Was it defined before this call?", name)
    if not new_req:
        output.warning_msgf(
            "requirement '{1}' was not found to add to requirement {0}. Was it defined before this call?", name, requirementname)
    common.extend_unique(tmp._values, new_req)
    


def Requirement(name):
    tmp = _added_types.get(name)
    if tmp:
        return tmp[0]

# setup default value for common stuff... some of this should move to tools that define them

# general


# general SDK
DefineRequirementSet('SDKINCLUDE', [requirement_internal('SDKINCLUDE', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('SDKLIB', [requirement_internal('SDKLIB', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('SDKBIN', [requirement_internal('SDKBIN', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('SDKCONFIG', [requirement_internal('SDKCONFIG', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('SDKDOC', [requirement_internal('SDKDOC', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('SDKHELP', [requirement_internal('SDKHELP', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('SDKMANPAGE', [requirement_internal('SDKMANPAGE', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('SDKDATA', [requirement_internal('SDKDATA', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('SDKMESSAGE', [requirement_internal('SDKMESSAGE', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('SDKRESOURCE', [requirement_internal('SDKRESOURCE', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('SDKSAMPLE', [requirement_internal('SDKSAMPLE', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('SDKTOPLEVEL', [requirement_internal('SDKTOPLEVEL', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('SDKPKGNO', [requirement_internal('SDKPKGNO', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('SDKAPI', [requirement_internal('SDKAPI', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('SDKTOOLS', [requirement_internal('SDKTOOLS', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('SDKPYTHON', [requirement_internal('SDKPYTHON', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('SDKSCRIPT', [requirement_internal('SDKSCRIPT', policy=REQ.Policy.ignore, listtype=True, internal=True)])


DefineRequirementSet('SDKTARGET', ['SDKBIN', 'SDKLIB'], weight=-5000)
DefineRequirementSet('SDKFILES', [
    'SDKINCLUDE',
    'SDKLIB',
    'SDKBIN',
    'SDKCONFIG',
    'SDKDOC',
    'SDKHELP',
    'SDKMANPAGE',
    'SDKDATA',
    'SDKMESSAGE',
    'SDKRESOURCE',
    'SDKSAMPLE',
    'SDKTOPLEVEL',
    'SDKPKGNO',
    'SDKAPI',
    'SDKTOOLS',
    'SDKPYTHON',
    'SDKSCRIPT'
], weight=-5000)

# general install
DefineRequirementSet('INSTALLINCLUDE', [requirement_internal(
    'INSTALLINCLUDE', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('INSTALLLIB', [requirement_internal('INSTALLLIB', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('INSTALLBIN', [requirement_internal('INSTALLBIN', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('INSTALLCONFIG', [requirement_internal(
    'INSTALLCONFIG', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('INSTALLDOC', [requirement_internal('INSTALLDOC', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('INSTALLHELP', [requirement_internal('INSTALLHELP', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('INSTALLMANPAGE', [requirement_internal(
    'INSTALLMANPAGE', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('INSTALLDATA', [requirement_internal('INSTALLDATA', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('INSTALLMESSAGE', [requirement_internal(
    'INSTALLMESSAGE', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('INSTALLRESOURCE', [requirement_internal(
    'INSTALLRESOURCE', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('INSTALLSAMPLE', [requirement_internal(
    'INSTALLSAMPLE', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('INSTALLTOPLEVEL', [requirement_internal(
    'INSTALLTOPLEVEL', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('INSTALLPKGNO', [requirement_internal('INSTALLPKGNO', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('INSTALLAPI', [requirement_internal('INSTALLAPI', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('INSTALLPYTHON', [requirement_internal(
    'INSTALLPYTHON', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('INSTALLSCRIPT', [requirement_internal(
    'INSTALLSCRIPT', policy=REQ.Policy.ignore, listtype=True, internal=True)])

DefineRequirementSet('INSTALLTARGET', ['INSTALLBIN', 'INSTALLLIB'], weight=-5000)
DefineRequirementSet('INSTALLFILES', [
    'INSTALLINCLUDE',
    'INSTALLLIB',
    'INSTALLBIN',
    'INSTALLCONFIG',
    'INSTALLDOC',
    'INSTALLHELP',
    'INSTALLMANPAGE',
    'INSTALLDATA',
    'INSTALLMESSAGE',
    'INSTALLRESOURCE',
    'INSTALLSAMPLE',
    'INSTALLTOPLEVEL',
    'INSTALLPKGNO',
    'INSTALLAPI',
    'INSTALLPYTHON',
    'INSTALLSCRIPT'
], weight=-5000)

DefineRequirementSet(
    'EXISTS', [
        requirement('EXISTS', public=False, listtype=False, policy=REQ.Policy.ignore, internal=True, mapto=lambda section: [""])]
)

# pkgconfig -- for better third party builds integration
DefineRequirementSet('PKG_CONFIG_PATH', [requirement('PKG_CONFIG_PATH', public=True, policy=REQ.Policy.ignore, internal=True)])
# help with third part builds ( cmake mostly in this case)
DefineRequirementSet('DESTDIR_PATH', [requirement('DESTDIR_PATH', public=True, listtype=False,
                                                  policy=REQ.Policy.ignore, internal=True, force_internal=True)])

# Packaging
DefineRequirementSet('RPM_PACKAGE_RUNPATH', [requirement('RPM_PACKAGE_RUNPATH', public=True,
                                                         listtype=True, policy=REQ.Policy.ignore, internal=True, force_internal=True)])

DefineRequirementSet('PKG_RPM', [requirement('PKG_RPM', public=False, listtype=False,
                                             policy=REQ.Policy.ignore, internal=True, force_internal=True)])
DefineRequirementSet('PKG_RPM_DEVEL', [requirement('PKG_RPM_DEVEL', public=False,
                                                   listtype=False, policy=REQ.Policy.ignore, internal=True, force_internal=True)])

DefineRequirementSet('PKG_DEFAULTS', ['PKG_RPM', 'PKG_RPM_DEVEL'], weight=-5000)

# C/C++ like
DefineRequirementSet('CPPPATH', [requirement('CPPPATH', public=True, policy=REQ.Policy.ignore)])
DefineRequirementSet('CPPDEFINES', [requirement('CPPDEFINES', public=True, policy=REQ.Policy.ignore)])
DefineRequirementSet('CXXFLAGS', [requirement('CXXFLAGS', public=True, policy=REQ.Policy.ignore)])
DefineRequirementSet('CFLAGS', [requirement('CFLAGS', public=True, policy=REQ.Policy.ignore)])
DefineRequirementSet('CCFLAGS', [requirement('CCFLAGS', public=True, policy=REQ.Policy.ignore)])
DefineRequirementSet('LINKFLAGS', [requirement('LINKFLAGS', public=True, policy=REQ.Policy.ignore)])
DefineRequirementSet('LIBPATH', [requirement('LIBPATH', public=True, policy=REQ.Policy.ignore)])
DefineRequirementSet('RPATHLINK', [requirement('RPATHLINK', public=True,
                                               policy=REQ.Policy.ignore, listtype=True, internal=False, force_internal=True)])

DefineRequirementSet('HEADERS', ['CPPPATH', 'CPPDEFINES', 'SDKINCLUDE'], weight=-5000)
DefineRequirementSet('LIBS', ['LIBPATH', requirement('LIBS', public=True, policy=REQ.Policy.ignore, listtype=True)], weight=-5000)

DefineRequirementSet('CPP_DEFAULTS', ['LIBS', 'HEADERS'], weight=-9000)
DefineRequirementSet('C_DEFAULTS', ['LIBS', 'HEADERS'], weight=-9000)


# defaults
DefineRequirementSet('DEFAULT', ['CPP_DEFAULTS', 'C_DEFAULTS', 'EXISTS', 'SDKLIB',
                                 'SDKBIN', 'PKG_CONFIG_PATH', "PKG_DEFAULTS", "DESTDIR_PATH", "RPATHLINK", "RPM_PACKAGE_RUNPATH"], weight=-10000)

# stuff to remove don't use this.. really don't use it.
DefineRequirementSet('ALL_DEFAULT', ['LIBS', 'HEADERS', 'CCFLAGS', 'CFLAGS', 'CXXFLAGS'],
                     policy.ReportingPolicy.warning, weight=-999999)
