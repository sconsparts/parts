import glb
import pattern
import common
import exportitem as Xp
import node_helpers
import api.output
import api.requirement
import errors

import os

import SCons.Script

g_sdked_files = set([])

def process_Sdk_Copy(env, target_dir, sources, create_sdk=True, do_clean=False):

    # make sure inputs are in good format
    target_dir = env.arg2nodes(target_dir)[0]
    # Some varibles
    out = []
    src_dir = []

    # go through sources to get the source items correctly processed
    for s in sources:

        if isinstance(s, pattern.Pattern):
            #print s.sub_dirs()
            t = s.src_dir.srcnode().abspath
            if t not in src_dir:
                src_dir.append(t)
            t, sr = s.target_source(target_dir.abspath)

            if create_sdk == False:
                out += sr#s.files(t)
            else:
                out += env.CCopyAs(target=t, source=sr)

            #print "Pattern type"
        elif isinstance(s, SCons.Node.FS.Dir):
            #get all file in the directory
            #... add code...

            t = s.srcnode().abspath
            if t not in src_dir:
                src_dir.append(t)
                #print t
            if create_sdk == False:
                out.append(s)
            else:
                out.extend(env.CCopy(target=target_dir, source=s))
            #print "Dir type"
        elif isinstance(s, SCons.Node.FS.File):
            #print s.abspath
            t = s.srcnode().dir.abspath
            if t not in src_dir:
                src_dir.append(t)
                #print t
            if create_sdk == False:
                out.append(s)
                #print s
            else:
                #print target_dir, s
                out.extend(env.CCopy(target=target_dir, source=s))
            #src.append(s)
            #print "File type"
        elif isinstance(s, SCons.Node.Node) or common.is_string(s):
            t = os.path.split(str(s))[0]
            if t not in src_dir:
                src_dir.append(t)
            if create_sdk == False:
                out.append(s)
            else:
                out.extend(env.CCopy(target=target_dir, source=s))
            #src.append(s)
        else:
            api.output.warning_msg('Unknown type "{0}" in process_Sdk_Copy() in sdk.py'.format(type(s)))

    #define Alias if we have a part being defined
    if create_sdk == True:
        g_sdked_files.update(out)

    # return a tuple of output files and the Src_dir list
    # might change this later to a list of the Source file instead
    return (out, src_dir)



def SdkItem(env, target_dir, sources, sub_dir='', post_fix='', export_info=[], add_to_path=True,
                auto_add_file=True, use_src_dir=False, use_build_dir=False, create_sdk=True):

    errors.SetPartStackFrameInfo(True)

    sources = SCons.Script.Flatten(sources)

    pobj = glb.engine._part_manager._from_env(env)

    # this is for classic formats and compatible behavior with 0.9
    pobj._sdk_or_installed_called = True

    target_paths = []

    target_dir_name = target_dir
    target_dir = env.Dir(target_dir_name)

    if sub_dir == '':
        dest_dir = target_dir
        # currenltly we always add that base path, since this is it,
        # setting to false reduces a extra duplication latter
        add_to_path = False
    else:
        dest_dir = env.Dir('./'+sub_dir, # To overcome the case when sub_dir starts with #
                directory=target_dir)

    do_clean = True

    if env['CREATE_SDK'] == False and create_sdk == True:
        create_sdk = False

    # Process the SDK COPY part of the SDK Item
    targets, source_dir = process_Sdk_Copy(env, dest_dir, sources, create_sdk, do_clean)

    if create_sdk == False and use_build_dir == True:
        target_dir = env.Dir('$BUILD_DIR')
    elif create_sdk == False and use_build_dir == False:
        use_src_dir = True


    if pobj is not None:

        #Process the Export of data values
        for _type, _prop in export_info:
            # add missing properties in map
            if pobj.DefiningSection.Exports.has_key(_prop) == False:
                pobj.DefiningSection.Exports[_prop] = [[]]
            # might add case that allow export of all directories
            if _type == Xp.EXPORT_TYPES.PATH and add_to_path == True:
                target_paths += Xp.export_path(env, [dest_dir], source_dir, pobj, _prop, use_src_dir, create_sdk)
                #This line is a hack till we can get a BKM out
                target_paths += Xp.export_path(env, [target_dir], source_dir, pobj, _prop, use_src_dir, create_sdk)
            elif _type == Xp.EXPORT_TYPES.PATH and add_to_path == False:
                target_paths += Xp.export_path(env, [target_dir], source_dir, pobj, _prop, use_src_dir, create_sdk)
            elif _type == Xp.EXPORT_TYPES.FILE and auto_add_file == True:
                files = Xp.export_file(env, targets, pobj, _prop)
            elif _type == Xp.EXPORT_TYPES.PATH_FILE:
                files = Xp.export_file_path(env, targets, pobj, _prop, ((create_sdk==False) or use_src_dir))
            else:
                pass
        if create_sdk == True:
            #if we are making an SDK add the node to the SDK list

            pobj._sdk_files.extend(targets)
            if not export_info:
                pass
            elif len(export_info) == 1 and export_info[0][0] == Xp.EXPORT_TYPES.PATH:
                pobj._create_sdk_data.append(('ExportItem', [export_info[0][1], common._make_reld(target_paths), False]))
            else:
                pobj._create_sdk_data.append(('SdkItem', [target_dir_name, common._make_rel(targets), sub_dir, post_fix, export_info, add_to_path, auto_add_file, True, use_build_dir, False]))

    tmp = target_dir_name[1:].replace('_', '')
    if create_sdk:
        env.ExportItem(tmp, targets, create_sdk, True)

    errors.ResetPartStackFrameInfo()
    return targets


def SdkInclude(env, sources, sub_dir='', add_to_path=None, use_src_dir=False, create_sdk=True):

    if add_to_path is None:
        add_to_path = env.get('SDK_INCLUDE_ADD_TO_PATH', False)
    ret = SdkItem(env, '$SDK_INCLUDE', sources, sub_dir, '', [(Xp.EXPORT_TYPES.PATH , 'CPPPATH')],
            add_to_path=add_to_path, auto_add_file=True, use_src_dir=use_src_dir,
            use_build_dir=False, create_sdk=create_sdk)
    return ret


def SdkLib(env, sources, sub_dir='', add_to_path=None, auto_add_libs=True, use_src_dir=False, create_sdk=True):

    if add_to_path is None:
        add_to_path = env.get('SDK_LIB_ADD_TO_PATH', True)
    ret = SdkItem(env, '$SDK_LIB', sources, sub_dir, '', [(Xp.EXPORT_TYPES.FILE , 'LIBS'), (Xp.EXPORT_TYPES.PATH , 'LIBPATH')],
            add_to_path=add_to_path, auto_add_file=auto_add_libs, use_src_dir=use_src_dir,
            use_build_dir=True, create_sdk=create_sdk)
    return ret

def SdkBin(env, sources, sub_dir='', create_sdk=True):

    ret = SdkItem(env, '$SDK_BIN', sources, sub_dir, '', [], create_sdk=create_sdk)
    return ret

def SdkConfig(env, sources, sub_dir='', create_sdk=True):

    ret = SdkItem(env, '$SDK_CONFIG', sources, sub_dir, '', [], create_sdk=create_sdk)
    return ret

def SdkDoc(env, sources, sub_dir='', create_sdk=True):

    ret = SdkItem(env, '$SDK_DOC', sources, sub_dir, '', [], create_sdk=create_sdk)
    return ret

def SdkHelp(env, sources, sub_dir='', create_sdk=True):

    ret = SdkItem(env, '$SDK_HELP', sources, sub_dir, '', [], create_sdk=create_sdk)
    return ret

def SdkManPage(env, sources, sub_dir='', create_sdk=True):

    ret = SdkItem(env, '$SDK_MANPAGE', sources, sub_dir, '', [], create_sdk=create_sdk)
    return ret

def SdkData(env, sources, sub_dir='', create_sdk=True):

    ret = SdkItem(env, '$SDK_DATA', sources, sub_dir, '', [], create_sdk=create_sdk)
    return ret

def SdkMessage(env, sources, sub_dir='', create_sdk=True):

    ret = SdkItem(env, '$SDK_MESSAGE', sources, sub_dir, '', [], create_sdk=create_sdk)
    return ret

def SdkResource(env, sources, sub_dir='', create_sdk=True):

    ret = SdkItem(env, '$SDK_RESOURCE', sources, sub_dir, '', [], create_sdk=create_sdk)
    return ret

def SdkSample(env, sources, sub_dir='', create_sdk=True):

    ret = SdkItem(env, '$SDK_SAMPLE', sources, sub_dir, '', [], create_sdk=create_sdk)
    return ret

def SdkTopLevel(env, sources, sub_dir='', create_sdk=True):

    ret = SdkItem(env, '$SDK_TOP_LEVEL', sources, sub_dir, '', [], create_sdk=create_sdk)
    return ret

def SdkNoPkg(env, sources, sub_dir='', create_sdk=True):

    ret = SdkItem(env, '$SDK_NO_PKG', sources, sub_dir, '', [], create_sdk=create_sdk)
    return ret

def SdkAPI(env, sources, sub_dir='', create_sdk=True):

    ret = SdkItem(env, '$SDK_API', sources, sub_dir, '', [], create_sdk=create_sdk)
    return ret

def SdkPython(env, sources, sub_dir='', create_sdk=True):

    ret = SdkItem(env, '$SDK_PYTHON', sources, sub_dir, '', [], create_sdk=create_sdk)
    return ret

def SdkScript(env, sources, sub_dir='', create_sdk=True):

    ret = SdkItem(env, '$SDK_SCRIPT', sources, sub_dir, '', [], create_sdk=create_sdk)
    return ret

def SdkPkgData(env, sources, sub_dir='',create_sdk=True):
    ret = SdkItem(env, '$SDK_PKGDATA', sources, sub_dir, '', [], create_sdk=create_sdk)
    return ret

def Sdk(env, sources, sub_dir='', add_to_path=True, auto_add_libs=True, use_src_dir=False, create_sdk=True):
    errors.SetPartStackFrameInfo(True)
    if sources == None:
        return
    if common.is_list(sources) == False:
        sources = [sources]
    sources = SCons.Script.Flatten(sources)
    out = []
    for i in sources:
        if isinstance(i, SCons.Node.FS.File)or isinstance(i, SCons.Node.Node) or common.is_string(i):
            try:
                the_file = i.attributes.FilterAs
            except AttributeError:
                the_file = i
            if common.is_catagory_file(env, 'SDK_LIB_PATTERN', the_file):
                out += SdkLib(env, [i], sub_dir=sub_dir, auto_add_libs=auto_add_libs,
                            add_to_path=add_to_path, use_src_dir=use_src_dir, create_sdk=create_sdk)
            elif common.is_catagory_file(env, 'SDK_BIN_PATTERN', the_file):
                out += SdkBin(env, [i], sub_dir=sub_dir, create_sdk=create_sdk)
            else:
                #print 'Miss', i
                pass
        elif isinstance(i, pattern.Pattern):
            for td in i.sub_dirs():
                for d in i.files(td):
                    if common.is_catagory_file(env, 'SDK_LIB_PATTERN', d):
                        if td !='':
                            tmp = SdkItem(env, '$SDK_LIB', [d], os.path.join(str(sub_dir), str(td)),
                                '', [(Xp.EXPORT_TYPES.FILE , 'LIBS'), (Xp.EXPORT_TYPES.PATH , 'LIBPATH')],
                                add_to_path=add_to_path, auto_add_file=auto_add_libs, use_src_dir=use_src_dir,
                                use_build_dir=True, create_sdk=create_sdk)
                        else:
                            tmp = SdkItem(env, '$SDK_LIB', [d], sub_dir, '',
                                [(Xp.EXPORT_TYPES.FILE , 'LIBS'), (Xp.EXPORT_TYPES.PATH , 'LIBPATH')],
                                add_to_path=add_to_path, auto_add_file=auto_add_libs, use_src_dir=use_src_dir,
                                use_build_dir=True, create_sdk=create_sdk)
                        if env['CREATE_SDK'] == True and create_sdk:
                            env.ExportItem('SDKLIB', tmp, create_sdk, True)
                        out += tmp

                    elif common.is_catagory_file(env, 'SDK_BIN_PATTERN', d):
                        if td !='':
                            tmp = SdkItem(env, '$SDK_BIN', [d],
                                    os.path.join(str(sub_dir), str(td)), '', [],
                                    create_sdk=create_sdk)
                        else:
                            tmp = SdkItem(env, '$SDK_BIN', [d], sub_dir, '', [], create_sdk=create_sdk)
                        if env['CREATE_SDK'] == True and create_sdk:
                            env.ExportItem('SDKBIN', tmp, create_sdk, True)
                        out += tmp
                    else:
                        pass
    errors.ResetPartStackFrameInfo()
    return out



#####################################################
## The SDK part file builder
#####################################################

def CreateSDK_SF(node, env, path):
    '''
    This is a scanner function for the target file
    This will return all node that this object depends on
    in that we want to mapp all files copied into the SDK here
    '''
    ret = []
    pobj = glb.engine._part_manager._from_env(env)
    # we want to depend on all direct dependant SDK files so we know they exist
    # otherwise this SDK file has little value
    for d in pobj.Depends:
        pdobj = d.part
        if pdobj is None:
            pass
        elif pdobj._sdk_file is None:
            ret.append(pdobj._file)
        else:
            ret.append(pdobj._sdk_file)

    # we want this depend on all the file that will be copied to the SDK area
    # so we know is this file exists the build for getting stuff in the SDK
    # has happened
    for t in pobj._sdk_files:
        ret.append("#%s" % t.path)
    return ret



def CreateSDK_BF(target, source, env):


    output = env._get_part_log_mapper()
    id = output.TaskStart('Generating SDK file for Part ' + str(os.path.split(target[0].path)[1][:-9]))

    # the part object for this sdk file we want to make
    pobj = glb.engine._part_manager._from_env(env)
    #get the version information
    ver_str = str(pobj.Version)
    # get the ShortName
    name = pobj.ShortName
    # get what we depend on.. need this to make a string of the depends on call
    comp = pobj.Depends
    comp_lst = []
    sdk_path = target[0].dir.path
    for c in comp:
        # we want to get the version of the component we depend on
        # however the component might not have been defined in the build
        tmp = c.resolve_alias(env)
        if tmp == '' or tmp is None:
            # we did not find anything
            # so we make the provided range
            exact_ver = str(c.version)
        else:
            # it was mapped so we map the exact version
            # as this is needed to make sure the sdk is used correctly
            exact_ver = str(c.part.Version)
        comp_lst += ['Component("'+c.name+'", "'+env.subst(exact_ver)+'", requires='+str(c.requires)+')']

    data = '''
#THIS FILE IS AUTO GENERATED
Import('*')

# Normal stuff that all Parts should have
PartName("''' + name + '''")
PartVersion("''' + ver_str + '''")
'''
    if comp_lst != []:
        data += '''DependsOn(['''+', '.join(comp_lst)+"])"
    data += '''
@build.config
def config(env):
    # This is to prevent SDK from generated by mistake another SDK
    env['CREATE_SDK'] = False

    #This prevents the SDK from being used with different configurations
    if not env.isConfigBasedOn("''' + env['CONFIG'] + '''"):
        env.PrintError("Parts generated SDK for part named ''' + env.subst('$PART_NAME') + ''' (alias of ''' + env.subst('$ALIAS') + \
        ''') needs to be build with ''' + env['CONFIG'] + ''' configuration, being build with",env['CONFIG'],"configuration)"

@build.emit
def emit(env):
    #Stuff we need to export
'''

    for i in pobj._create_sdk_data:
        files = []
        data += common.func_gen(env, sdk_path, i[0], i[1])+'\n'


    with open(str(target[0]), 'wb') as f:
        f.write(data)

    output.TaskEnd(id, 0)
    return None

def CreateSDK_StrF(target, source, env):
    return 'Parts: Generating SDK file for Part ' + str(os.path.split(target[0].path)[1][:-9])

def CreateSDK_Emit(target, source, env):
    tf = env.subst('$PART_NAME') + '_' + env.subst('$PART_VERSION')
    tout = [os.path.join('$SDK_ROOT',tf + '.sdk.parts')]
    return (tout, source)

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.SdkInclude = SdkInclude
SConsEnvironment.SdkLib = SdkLib
SConsEnvironment.SdkBin = SdkBin
SConsEnvironment.Sdk = Sdk
SConsEnvironment.SdkTarget = Sdk
SConsEnvironment.SdkConfig = SdkConfig
SConsEnvironment.SdkDoc = SdkDoc
SConsEnvironment.SdkHelp = SdkHelp
SConsEnvironment.SdkManPage = SdkManPage
SConsEnvironment.SdkData = SdkData
SConsEnvironment.SdkMessage = SdkMessage
SConsEnvironment.SdkResource = SdkResource
SConsEnvironment.SdkItem = SdkItem
SConsEnvironment.SdkSample = SdkSample
SConsEnvironment.SdkTopLevel = SdkTopLevel
SConsEnvironment.SdkNoPkg = SdkNoPkg
SConsEnvironment.SdkPkgNo = SdkNoPkg
SConsEnvironment.SdkAPI = SdkAPI
SConsEnvironment.SdkPython = SdkPython
SConsEnvironment.SdkScript = SdkScript
SConsEnvironment.SdkPkgData = SdkPkgData


api.register.add_builder('__CreateSDKBuilder__', SCons.Builder.Builder(
        action=SCons.Script.Action(CreateSDK_BF, CreateSDK_StrF,
            varlist=['PART_NAME', 'ALIAS']),
        emitter=CreateSDK_Emit,
        target_scanner=SCons.Scanner.Base(CreateSDK_SF)
        ))
import datetime
# add configuartion varaible
api.register.add_variable("DATE_STAMP", datetime.datetime.now().strftime('%Y%m%d%H%M'), '')

api.register.add_variable('SDK_ROOT',
        '#_sdks/${CONFIG}_${TARGET_PLATFORM}_${TOOLCHAIN.replace(",", "_")}/${PART_ROOT_NAME}_${PART_VERSION}${"_%s"%PART_ROOT_SIG if PART_ROOT_SIG!="" else ""}',
                    'Root Directory used for copy SDKs to')
api.register.add_variable('SDK_LIB_ROOT', '$SDK_ROOT/lib', 'Full SDK directory for the lib concept')
api.register.add_variable('SDK_BIN_ROOT', '$SDK_ROOT/bin', 'Full SDK directory for the bin concept')
api.register.add_variable('SDK_INCLUDE_ROOT', '$SDK_ROOT/include', 'Full SDK directory for the include or header concept')
api.register.add_variable('SDK_LIB', '$SDK_LIB_ROOT', 'Full SDK directory for the lib concept')
api.register.add_variable('SDK_BIN', '$SDK_BIN_ROOT', 'Full SDK directory for the bin concept')
api.register.add_variable('SDK_INCLUDE', '$SDK_INCLUDE_ROOT', 'Full SDK directory for the include or header concept')
api.register.add_variable('SDK_API', '$SDK_ROOT/API', 'Full SDK directory for the API concept')
api.register.add_variable('SDK_CONFIG', '$SDK_ROOT/config', 'Full SDK directory for the configuration file concept')
api.register.add_variable('SDK_DOC', '$SDK_ROOT/doc', 'Full SDK directory for the documenation concept')
api.register.add_variable('SDK_HELP', '$SDK_ROOT/help', 'Full SDK directory for the help concept')
api.register.add_variable('SDK_MANPAGE', '$SDK_ROOT/man', 'Full SDK directory for the manpage concept')
api.register.add_variable('SDK_DATA', '$SDK_ROOT/data', 'Full SDK directory for the generic data concept')
api.register.add_variable('SDK_MESSAGE', '$SDK_ROOT/message', 'Full SDK directory for the messages (catalogs) concept')
api.register.add_variable('SDK_RESOURCE', '$SDK_ROOT/resource', 'Full SDK directory for the resource concept')
api.register.add_variable('SDK_SAMPLE', '$SDK_ROOT/sample', 'Full SDK directory for the sample concept')
api.register.add_variable('SDK_TOP_LEVEL', '$SDK_ROOT/TOP_LEVEL', 'Full SDK directory for the file that get installed as the top level (such readme.txt)')
api.register.add_variable('SDK_NO_PKG', '$SDK_ROOT/NO_INSTALL', 'For files needed for the product in some way, but should not be added in the final install package')
api.register.add_variable('SDK_PYTHON', '$SDK_ROOT/python', 'Full SDK directory for the python file concept')
api.register.add_variable('SDK_SCRIPT', '$SDK_ROOT/scripts', 'Full SDK directory for general script file concept')
api.register.add_variable('SDK_PKGDATA', '$SDK_ROOT/pkgdata', 'Full SDK directory for general script file concept')

api.register.add_bool_variable('SDK_ADD_TO_PATH', True, 'Controls is the Path provided is added along with the base SDK include path to dependent components')


api.register.add_bool_variable('USE_SRC_DIR', False, 'Controls is the SDK or Src directory of the Part is passed to dependent parts, useful for debug builds')
api.register.add_bool_variable('CREATE_SDK', True, 'Controls if the SDK should be created and used')

api.register.add_list_variable('SDK_LIB_PATTERN', ['*.lib', '*.LIB', '*.a', '*.A', '*.so', '*.sl', '*.so.*', '*.sl.*', '*.so-gz', '*.dylib'], 'filter of file patterns use to match lib type files')
if 'win32' == glb._host_sys:
    api.register.add_list_variable('SDK_BIN_PATTERN', ['*.dll', '*.DLL', '*.exe', '*.EXE', '*.com', '*.COM', '*.pdb', '*.PDB'], 'filter of file patterns use to match bin type files')
else:
    api.register.add_list_variable('SDK_BIN_PATTERN', ['*'], 'filter of file patterns use to match lib type files')

# vim: set et ts=4 sw=4 ai ft=python :

