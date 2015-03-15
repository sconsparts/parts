
from .. import glb
from .. import platform_info
import output


def AddArchitecture(arch_alias,arch = '', change_arch_map = False):    
    if arch == '':
        arch = arch_alias
    if (arch_alias in glb.arch_map) and (not change_arch_map): 
        output.warning_msg(arch_alias,"already exists as a Valid Platform\n  To force a change use AddArchitecture(arch_alias,arch,True)")
    else:
        glb.arch_map[arch_alias] = arch 
    platform_info.UpdateValidArchList()
        

def AddOS(os_alias,os = '', change_os_map = False):
    if os == '':
        os = os_alias
    if (os_alias in glb.os_map) and (not change_os_map): 
        output.warning_msg(os_alias,"already exists as a Valid Platform\n  To force a change use AddOS(os_alias,os,True)")
    else:
        glb.os_map[os_alias] = os 
    platform_info.UpdateValidOSList()
