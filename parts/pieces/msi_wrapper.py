import parts.errors
import parts.common as common
import parts.glb as glb
from SCons.Debug import logInstanceCreation

def map_msi_builder(env, target, sources, stackframe, **kw):
    def msi_builder():
        
        wxs_files = []
        def control_sources(node):
            global wxs_files
            if env.MetaTagValue(node, 'category', 'package') == 'PKGDATA':
                if 'msi' in env.MetaTagValue(node, 'types', 'package', ['msi']):   
                    if node.ID.endswith(".wxs"):
                        # these are wxs file we need to build
                        wxs_files.extend(env.CCopy('.',node))
                    else:                
                        # these are I don't know what.. might be resourecs for wxs files.
                        env.CCopy('.',node)
                return False
            return True
        msi_name=target
        # for each group ( source is a list of package groups
        wix_paths=[]
        for g in sources:
            #get files from group
            files = env.GetPackageGroupFiles(g)
            # filter sources and copy to staging area to make a file list off of
            pkg_nodes=[]        
            src=filter(control_sources,files)
            if not src:                
                continue
            for n in src:
                #get Package directory for node
                pk_type=env.MetaTagValue(n, 'category','package')
                pkg_dir="${{PACKAGE_{0}}}".format(pk_type)
                # generate file for group once
                pkg_nodes.append(env.Entry('${{BUILD_DIR}}/_msi/{0}/{1}/{2}'.format(g,pkg_dir,env.Dir(n.env['INSTALL_{0}'.format(pk_type)]).rel_path(n))))
            # copy filea with hard links to save space
            grp_sources = env.CCopyAs(pkg_nodes, src, CCOPY_LOGIC='hard-copy')
            # run Heat on directory to make file list
            wxs_files.extend(env._heat("${{BUILD_DIR}}/{0}".format(g),"${{BUILD_DIR}}/_msi/{0}".format(g)))

        print "wxs_files to build =",wxs_files
        #env.Append("WIXPPPATH",)
        env.MSI(target,wxs_files)
        




        #new_sources, _ = env.Override(kw).GetFilesFromPackageGroups(target, sources, stackframe)
        
        ## copy source node to build area, have to keep directory structure
        ## Following logic will maintain the directory structure, e.g
        ## /bin/setup.py
        ## try make a hardlink for the source files else do a full copy
        
        ##print env.PackageGroups()
        ## get files from individual package group
        ## run heat on the them

        #def control_sources(node):
        #    global spec_in
        #    if env.MetaTagValue(node, 'category', 'package') == 'PKGDATA':
        #        if 'msi' in env.MetaTagValue(node, 'types', 'package', ['msi']):                   
        #                env.CCopy('${BUILD_DIR}/CONTROLFILES',node)
        #        return False
        #    return True

        #src = filter(control_sources,new_sources)
        
        #pkg_nodes = []
        #for n in src:
        #    #get Package directory for node
        #    pk_type = env.MetaTagValue(n, 'category','package')            
        #    pkg_dir = "${{PACKAGE_{0}}}".format(pk_type)            
        #    pkg_nodes.append('${{BUILD_DIR}}/{0}'.format(env.Dir(n.env['INSTALL_{0}'.format(pk_type)]).rel_path(n)))        
        #ret = env.CCopyAs(pkg_nodes, src, CCOPY_LOGIC='hard-copy')        
        ##print env.subst(pkg_nodes),90
        
        ##=================================================================================
        ## use heat to generate the wxs files for individual package-group.
        ## use candle to compile the wxs files
        ## use light to link the wixobj files.
        
        ##==================================================================================
        ## really call the builder so everything is setup correctly
        ## new sources are added along with control sources (files installed
        ## with PkgData for msi package)
        ## to the target
        
        #test_wxs = env._heat('${BUILD_DIR}/test.wxs', ret, SRC_DIR="${BUILD_DIR}")
        ##env._candle('${BUILD_DIR}/test.wixobj', test_wxs)
    return msi_builder

def MsiPackage_wrapper(env,target,sources,**kw):
    # currently we assume all sources are Group values
    # will probally change this once we understand better

    target = common.make_list(target)
    sources = common.make_list(sources)
    #print sources,23
    #print env.subst(target),24
    
    if len(target) > 1:
        raise SCons.Errors.UserError('Only one target is allowed.')
    
    if str(target[0]).endswith('.msi'):
        target = [env.Dir(".").File(target[0])]
    else:
        target = [env.Dir(".").File(target[0] + ".msi")]

    sources = [env.subst(s) for s in sources]
    #print env.subst(target),25

    glb.engine.add_preprocess_logic_queue(map_msi_builder(env, target[0], sources,
                parts.errors.GetPartStackFrameInfo(), **kw))
    return target

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

SConsEnvironment.MSIPackage = MsiPackage_wrapper