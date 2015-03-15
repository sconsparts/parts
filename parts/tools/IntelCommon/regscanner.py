import SCons.Util
import sys
import re
import parts.tools.Common.Finders as Finders
import common

from SCons.Debug import logInstanceCreation

# this are primary for finding Intel compilers on windows platforms
# file_scanner is for finding files on Posix/Linux systems


#this is a general scanner for all version till version 11.1
class reg_scanner(object):
    def __init__(self,regkeys,pattern,arch,env,ver):
        if __debug__: logInstanceCreation(self)
        self.pattern=pattern
        self.reg_keys=regkeys
        self.arch=arch
        self.env_var=Finders.EnvFinder(env,arch)
        self.cache=None
        self.ver=ver

    def scan(self):
        # search for all known location for a give version
        if self.cache is None:
            # what we will want to return
            ret={}
            # pattern to match on
            reg=re.compile(self.pattern, re.I)
            # The erg key we will open
            k=None
            # for each key location
            for key in self.reg_keys:
                try:
                    # try to open key
                    k = SCons.Util.RegOpenKeyEx(SCons.Util.HKEY_LOCAL_MACHINE,
                                                key)
                    keyname=key
                    break
                except WindowsError:
                    # if not try again
                    pass
            #if this is none we have an error
            if k is None:
                #print "Error 1... No Intel compilers found via std install means"
                return

            i = 0
            try:
                while i < 50: #Don't loop forever, just in case of massive failure
                    # iterate over the key to get valid version numbers
                    subkey = SCons.Util.RegEnumKey(k, i) # raises EnvironmentError
                    #parse to see if we got match
                    result=reg.match(subkey)
                    if result:
                        # form up full key name to test for install
                        keyname2=keyname+"\\"+subkey+"\\"+self.arch+"\\ProductDir"
                        try:
                            #try to get value
                            path = SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE,
                                             keyname2)[0]

                            ret[".".join(result.groups())]=path
                        except WindowsError:
                            #key not registry.. so we ignore
                            pass
                    i=i+1
            except EnvironmentError:
            # no more subkeys
                pass
            if ret =={}:
                # ctest env
                ret = self.env_var()
                if ret is not None:
                    ret[self.ver]=ret
            self.cache=ret
        return self.cache

    def resolve_version(self,version):
        tmp=self.scan()
        if tmp is None:
            return None
        k=tmp.keys()
        #k.reverse()
        for i in k:
            if common.MatchVersionNumbers(version,i):
                return i
        return None

    def resolve(self,ver):
        tmp=self.scan()
        if tmp is None:
            return None
        k=tmp.keys()
        #k.reverse()
        for i in k:
            if common.MatchVersionNumbers(ver,i):
                return tmp[i]
        return None


#this is a general scanner for all version at version 11.1 (and beyond??)
class reg_scanner2(object):
    def __init__(self,regkeys,pattern,arch,env,ver):
        if __debug__: logInstanceCreation(self)
        self.pattern=pattern
        self.reg_keys=regkeys
        self.arch=arch
        self.env_var=Finders.EnvFinder(env,arch)
        self.cache=None
        self.ver=ver


    def scan(self):
        # search for all known location for a give version
        if self.cache is None:
            # what we will want to return
            ret={}
            # pattern to match on
            reg=re.compile(self.pattern, re.I)
            # The erg key we will open
            k=None
            # for each key location
            for key in self.reg_keys:
                try:
                    # try to open key
                    k = SCons.Util.RegOpenKeyEx(SCons.Util.HKEY_LOCAL_MACHINE,
                                                key)
                    keyname=key
                    break
                except WindowsError:
                    # if not try again
                    pass
            #if this is none we have an error
            if k is None:
                #print "Error 1... No Intel compilers found via std install means"
                return

            i = 0
            try:
                while i < 50: #Don't loop forever, just in case of massive failure
                    # iterate over the key to get valid version numbers
                    subkey = SCons.Util.RegEnumKey(k, i) # raises EnvironmentError
                    #parse to see if we got match
                    result=reg.match(subkey)

                    if result:
                        # form up full key name to test for install
                        #keyname=keyname+"\\"+subkey+"\\C++\\"+self.arch+"\\ProductDir"
                        keyname1=keyname+"\\"+subkey+"\\C++\\ProductDir"

                        try:
                            #try to get value
                            path = SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE,
                                             keyname1)[0]


                            # and check to see if we have this arch version installed
                            keyname1=keyname+"\\"+subkey+"\\C++\\"+self.arch+"\\DisplayString"
                            SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE,
                                             keyname1)
                            # got value so we make up all version that this could match on
                            keyname1=keyname+"\\"+subkey+"\\C++\\Major Version"
                            va=SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE,
                                             keyname1)[0]
                            keyname1=keyname+"\\"+subkey+"\\C++\\Minor Version"
                            vb=SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE,
                                             keyname1)[0]
                            vc=subkey
                            tmp=".".join([str(va),str(vb),vc])

                            ret[tmp]=path
                        except WindowsError:
                            #key not registry.. so we ignore
                            pass
                    i=i+1
            except EnvironmentError:
            # no more subkeys
                pass
            if ret =={}:
                # ctest env
                ret = self.env_var()
                if ret is not None:
                    ret[self.ver]=ret
            self.cache=ret

        return self.cache

    def resolve_version(self,version):
        tmp=self.scan()
        if tmp is None:
            return None
        k=tmp.keys()
        #k.reverse()
        for i in k:
            if common.MatchVersionNumbers(version,i):
                return i
        return None

    def resolve(self,ver):
        tmp=self.scan()
        if tmp is None:
            return None
        k=tmp.keys()
        #k.reverse()
        for i in k:
            if common.MatchVersionNumbers(ver,i):
                return tmp[i]
        return None


#this is a general scanner for all version till version 12.0
class reg_scanner_v12(object):
    def __init__(self,regkeys,subkey_path,env_var):
        if __debug__: logInstanceCreation(self)
        # the root reg keys to scan
        self.reg_keys=regkeys
        # the subkey path
        self.subkey_path=subkey_path

        self.env_var=Finders.EnvFinder(env_var)
        self.cache=None

    def scan(self):
        '''
        '''
        # the 12 compiler on windows require a two step look up process
        # step on is to get a GUID value that is part of the path to the keys we
        # really want to read, such ProductDir.

        if self.cache is None:
            # what we will want to return
            ret={}
            keyname=None
            # get the root Req Key.
            for key in self.reg_keys:
                try:
                    # try to open key
                    k = SCons.Util.RegOpenKeyEx(SCons.Util.HKEY_LOCAL_MACHINE,
                                                key)
                    keyname=key
                    break
                except WindowsError:
                    # if not try again
                    pass

            #if this is none we have an error
            if keyname is None:
                #print "Error 1... No Intel compilers found via std install means"
                return

            root_key=key
            subkey="{0}{1}\\SubKey".format(root_key,self.subkey_path)
            #get the SubKey
            try:
                # try to open key
                k=SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE,
                                             subkey)[0]
                subkey=k
            except WindowsError:
                #key not registry.. nothing to find
                return

            fullrootkey="{0}\\{1}\\{2}".format(root_key,subkey,"C++")

            try:
                # Get path
                keyname1=fullrootkey+"\\ProductDir"
                path = SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE,
                                             keyname1)[0]
                # got value so we make up all version that this could match on
                keyname1=fullrootkey+"\\Major Version"
                va=SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE,
                                    keyname1)[0]
                keyname1=fullrootkey+"\\Minor Version"
                vb=SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE,
                                    keyname1)[0]
                keyname1=fullrootkey+"\\Revision"
                vc=SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE,
                                    keyname1)[0]

                tmp=".".join([str(va),str(vb),str(vc)])
                ret[tmp]=path

            except WindowsError:
                #key not registry.. nothing to find
                return

            if ret =={}:
                # ctest env
                ret = self.env_var()
                if ret is not None:
                    ret[self.ver]=ret
            self.cache=ret

        return self.cache


    def resolve_version(self,version):
        tmp=self.scan()
        if tmp is None:
            return None
        k=tmp.keys()
        #k.reverse()
        for i in k:
            if common.MatchVersionNumbers(version,i):
                return i
        return None

    def resolve(self,ver):
        tmp=self.scan()
        if tmp is None:
            return None
        k=tmp.keys()
        #k.reverse()
        for i in k:
            if common.MatchVersionNumbers(ver,i):
                return tmp[i]
        return None
