import parts.errors
import parts.common as common
import parts.glb as glb
from SCons.Debug import logInstanceCreation

def map_msi_builder(env, target, sources, stackframe, **kw):
    def msi_builder():
        new_sources, _ = env.Override(kw).GetFilesFromPackageGroups(target, sources, stackframe)
        control_sources=[]
        
        # function to filter the files installed with PkgData from new_sources,
        # if packagetype mentioned is msi

        def filter_func(node, ctr_nodes):
            if env.MetaTagValue(node,'category','package')=='PKGDATA':
                if 'msi' in env.MetaTagValue(node, 'types', 'package', ['msi']):
                    ctr_nodes+=env.CCopy('${BUILD_DIR}', node)
                return False
            return True

        new_sources=filter(lambda x: filter_func(x, control_sources), new_sources)

        # copy source node to build area, have to keep directory structure
        # Following logic will maintain the directory structure, e.g /bin/setup.py
        # try make a hardlink for the source files else do a full copy
        path_len=len(env.subst('${INSTALL_ROOT}'))
        new_sources=env.CCopyAs(
                ['${{BUILD_DIR}}/{0}'.format(n.ID[path_len:]) for n in new_sources ],
                new_sources,
                CCOPY_LOGIC='hard-copy'
                )

        # really call the builder so everything is setup correctly
        # new sources are added along with control sources (files installed with PkgData for msi package)
        # to the target
        for s in control_sources:
            if (s.ID).endswith('wxs'):
                wxsobj = env.WixObject(s)

        env.MSI(target, source = wxsobj)
    return msi_builder

def MsiPackage_wrapper(env,target,sources,**kw):
    # currently we assume all sources are Group values
    # will probally change this once we understand better

    target = common.make_list(target)
    sources= common.make_list(sources)

    if len(target) > 1:
        raise SCons.Errors.UserError('Only one target is allowed.')
    
    if str(target[0]).endswith('.msi'):
        target=[env.Dir(".").File(target[0])]
    else:
        target=[env.Dir(".").File(target[0]+".msi")]

    sources=[env.subst(s) for s in sources]

    glb.engine.add_preprocess_logic_queue(map_msi_builder(env, target[0], sources,
                parts.errors.GetPartStackFrameInfo(), **kw))
    return target

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

SConsEnvironment.MSIPackage=MsiPackage_wrapper