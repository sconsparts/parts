import parts.errors
import parts.common as common
import parts.glb as glb
from SCons.Debug import logInstanceCreation

def map_msi_builder(env, target, sources, stackframe, **kw):
    def msi_builder():

        wxs_files = []
        def control_sources(node):

            if env.MetaTagValue(node, 'category', 'package') == 'PKGDATA':
                if 'msi' in env.MetaTagValue(node, 'types', 'package', ['msi']):
                    if node.ID.endswith(".wxs"):
                        # these are wxs file we need to build
                        wxs_files.extend(env.CCopy('${BUILD_DIR}',node))
                    else:
                        # these are I don't know what.. might be resourecs for wxs files.
                        env.CCopy('${BUILD_DIR}',node)
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
            env.Append(WIXFILEPATH=["${{BUILD_DIR}}/_msi/{0}".format(g)])
            wxs_files.extend(env._heat("${{BUILD_DIR}}/{0}".format(g),"${{BUILD_DIR}}/_msi/{0}".format(g)))
        env.MSI(target,wxs_files)

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
        target = [env.Dir(".").File(env.subst(target[0]))]
    else:
        target = [env.Dir(".").File(env.subst(target[0]) + ".msi")]

    sources = [env.subst(s) for s in sources]
    #print env.subst(target),25

    glb.engine.add_preprocess_logic_queue(map_msi_builder(env, target[0], sources,
                parts.errors.GetPartStackFrameInfo(), **kw))
    return target

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

SConsEnvironment.MSIPackage = MsiPackage_wrapper