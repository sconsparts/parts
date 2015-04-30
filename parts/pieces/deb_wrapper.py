import SCons.Script
import parts.api as api
import parts.errors
import parts.common as common
import parts.glb as glb
import shutil, os

def deb_wrapper_mapper(env, target, sources, **kw):
    def deb_wrapper():

        #############################################
        # getting all the sources
        new_sources, _ = env.Override(kw).GetFilesFromPackageGroups(target, sources)

        #############################################
        ## Sort files in to source group and to control group
        def filter_func(node):
            if env.MetaTagValue(node, 'category', 'package')=='PKGDATA':
                if 'dpkg' in env.MetaTagValue(node, 'types', 'package', ['dpkg','deb','DEB']):
                    env.CCopy('${{BUILD_DIR}}/_dpkg/{0}/debian'.format(target.name[:-4]), node)
                return False
            return True

        src=filter(filter_func,new_sources)

        pkg_nodes = []
        for n in src:
            pk_type=env.MetaTagValue(n, 'category','package')
            pkg_dir="${{PACKAGE_{0}}}".format(pk_type)
            pkg_nodes.append(env.Entry('${{BUILD_DIR}}/_dpkg/{0}/{1}/{2}/{3}'.format(target.name[:-4],target.name[:-4],pkg_dir,env.Dir(n.env['INSTALL_{0}'.format(pk_type)]).rel_path(n))))

        #############################################
        ##create the source gz file
        ret = env.CCopyAs(pkg_nodes, src, CCOPY_LOGIC='hard-copy')
        Tar_Filename = target.name
        Tar_Filename=Tar_Filename.replace('-', '_')
        #############################################
        ##create the source gz file
        env.TarGzFile('${{BUILD_DIR}}/_dpkg/{0}.orig.tar.gz'.format(Tar_Filename[:-4]), src, SRC_DIR="$INSTALL_ROOT")

        env._dpkg(target, '${{BUILD_DIR}}/_dpkg/{0}'.format(target.name[:-4]))
    return deb_wrapper
     

def dpkg_wrapper(env, target, sources, **kw):
    # currently we assume all sources are Group values
    # will probally change this once we understand better

    target = common.make_list(target)
    sources= common.make_list(sources)

    if len(target) > 1:
        raise SCons.Errors.UserError('Only one target is allowed.')

    if str(target[0]).endswith('.deb'):
        target=[env.Dir(".").File(target[0])]
    else:
        target=[env.Dir(".").File(target[0]+".deb")]

    # subst all source values to get finial package group names
    sources=[env.subst(s) for s in sources]

    # delay real work till we have everything loaded
    glb.engine.add_preprocess_logic_queue(deb_wrapper_mapper(env, target[0], sources, **kw))
                
    return target


# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

SConsEnvironment.DPKGPackage=dpkg_wrapper