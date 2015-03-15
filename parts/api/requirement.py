
from .. import common
from .. import policy

from ..requirement import DefineRequirementSet, requirement,REQ,requirement_internal
          
# setup default value for common stuff... some of this should move to tools that define them

# general


#general SDK
DefineRequirementSet('SDKINCLUDE',[requirement_internal('SDKINCLUDE',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('SDKLIB',[requirement_internal('SDKLIB',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('SDKBIN',[requirement_internal('SDKBIN',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('SDKCONFIG',[requirement_internal('SDKCONFIG',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('SDKDOC',[requirement_internal('SDKDOC',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('SDKHELP',[requirement_internal('SDKHELP',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('SDKMANPAGE',[requirement_internal('SDKMANPAGE',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('SDKDATA',[requirement_internal('SDKDATA',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('SDKMESSAGE',[requirement_internal('SDKMESSAGE',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('SDKRESOURCE',[requirement_internal('SDKRESOURCE',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('SDKSAMPLE',[requirement_internal('SDKSAMPLE',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('SDKTOPLEVEL',[requirement_internal('SDKTOPLEVEL',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('SDKPKGNO',[requirement_internal('SDKPKGNO',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('SDKAPI',[requirement_internal('SDKAPI',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('SDKPYTHON',[requirement_internal('SDKPYTHON',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('SDKSCRIPT',[requirement_internal('SDKSCRIPT',policy=REQ.Policy.ignore,listtype=True,internal=True)])

DefineRequirementSet('SDKTARGET',['SDKBIN','SDKLIB'],weight=-5000)
DefineRequirementSet('SDKFILES',[
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
                        'SDKPYTHON',
                        'SDKSCRIPT'
                        ],weight=-5000)

#general install
DefineRequirementSet('INSTALLINCLUDE',[requirement_internal('INSTALLINCLUDE',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('INSTALLLIB',[requirement_internal('INSTALLLIB',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('INSTALLBIN',[requirement_internal('INSTALLBIN',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('INSTALLCONFIG',[requirement_internal('INSTALLCONFIG',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('INSTALLDOC',[requirement_internal('INSTALLDOC',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('INSTALLHELP',[requirement_internal('INSTALLHELP',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('INSTALLMANPAGE',[requirement_internal('INSTALLMANPAGE',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('INSTALLDATA',[requirement_internal('INSTALLDATA',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('INSTALLMESSAGE',[requirement_internal('INSTALLMESSAGE',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('INSTALLRESOURCE',[requirement_internal('INSTALLRESOURCE',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('INSTALLSAMPLE',[requirement_internal('INSTALLSAMPLE',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('INSTALLTOPLEVEL',[requirement_internal('INSTALLTOPLEVEL',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('INSTALLPKGNO',[requirement_internal('INSTALLPKGNO',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('INSTALLAPI',[requirement_internal('INSTALLAPI',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('INSTALLPYTHON',[requirement_internal('INSTALLPYTHON',policy=REQ.Policy.ignore,listtype=True,internal=True)])
DefineRequirementSet('INSTALLSCRIPT',[requirement_internal('INSTALLSCRIPT',policy=REQ.Policy.ignore,listtype=True,internal=True)])

DefineRequirementSet('INSTALLTARGET',['INSTALLBIN','INSTALLLIB'],weight=-5000)
DefineRequirementSet('INSTALLFILES',[
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
                        ],weight=-5000)

DefineRequirementSet('EXISTS',['INSTALLFILES'])

# C/C++ like
DefineRequirementSet('CPPPATH',[requirement('CPPPATH',public=True,policy=REQ.Policy.ignore)])
DefineRequirementSet('CPPDEFINES',[requirement('CPPDEFINES',public=True,policy=REQ.Policy.ignore)])
DefineRequirementSet('CXXFLAGS',[requirement('CXXFLAGS',public=True,policy=REQ.Policy.ignore)])
DefineRequirementSet('CFLAGS',[requirement('CFLAGS',public=True,policy=REQ.Policy.ignore)])
DefineRequirementSet('CCFLAGS',[requirement('CCFLAGS',public=True,policy=REQ.Policy.ignore)])
DefineRequirementSet('LINKFLAGS',[requirement('LINKFLAGS',public=True,policy=REQ.Policy.ignore)])
DefineRequirementSet('LIBPATH',[requirement('LIBPATH',public=True,policy=REQ.Policy.ignore)])

DefineRequirementSet('HEADERS',['CPPPATH','CPPDEFINES','SDKINCLUDE'],weight=-5000)
DefineRequirementSet('LIBS',['LIBPATH',requirement('LIBS',public=True,policy=REQ.Policy.ignore,listtype=True)],weight=-5000)

DefineRequirementSet('CPP_DEFAULTS',['LIBS','HEADERS'],weight=-9000)
DefineRequirementSet('C_DEFAULTS',['LIBS','HEADERS'],weight=-9000)

# defaults
DefineRequirementSet('DEFAULT',['CPP_DEFAULTS','C_DEFAULTS','INSTALLFILES','SDKLIB','SDKBIN'],weight=-10000)

# stuff to remove don't use this.. really don't use it.
DefineRequirementSet('ALL_DEFAULT',['LIBS','HEADERS','CCFLAGS','CFLAGS','CXXFLAGS'],policy.ReportingPolicy.warning,weight=-999999)
