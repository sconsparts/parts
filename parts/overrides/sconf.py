

import SCons.SConf

# test to see if we have the function.. else backport it
# this is needed to support any version pre-Scons 2.4
try:
    SCons.SConf.NeedConfigHBuilder
except:

    def NeedConfigHBuilder():
        if len(SCons.SConf._ac_config_hs) == 0:
           return False
        else:
           return True

    SCons.SConf.NeedConfigHBuilder=NeedConfigHBuilder
