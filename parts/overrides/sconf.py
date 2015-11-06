

import SCons.SConf

# test to see if we have the function.. else backport it
try:
    SCons.SConf.NeedConfigHBuilder
except:

    def NeedConfigHBuilder():
        if len(_ac_config_hs) == 0:
           return False
        else:
           return True

    SCons.SConf.NeedConfigHBuilder=NeedConfigHBuilder
