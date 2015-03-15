''' This is the script which can used as generic package_wrapper
    for all the archive builders including "tar","tar.gz","tar.bz2"
    "bz2","zip", "tgz"'''

import parts.errors
import parts.common as common
import parts.glb as glb
from SCons.Debug import logInstanceCreation

def map_archive_builder(env, target, sources, archive_type, stackframe, **kw):
    def archive_builder():
        new_sources, _ = env.Override(kw).GetFilesFromPackageGroups(target, sources, stackframe)
        control_sources=[]

        #for proper formatting of the package type to be used as archive builder type
        # without throwing any error.

        archive_type_proper = archive_type.lower().title().replace('.','')

        # function to filter files depending on the package type associated

        def _is_control_file_type(node, pkg_type, ctr_nodes):
            pkg_type = archive_type.lower().replace('.','')
            if pkg_type in env.MetaTagValue(node, 'types', 'package', [pkg_type]):
                ctr_nodes+=env.CCopy('${{BUILD_DIR}}/_{1}/{0}/'.format(target, archive_type_proper), node)

        # function to filter the files installed with PkgData from new_sources,
        # if packagetype mentioned is tar or tar.gz or tar.bz2 or bz2 or zip

        def is_source_file(node,ctr_nodes):
            if env.MetaTagValue(node, 'category','package')=='PKGDATA':
                _is_control_file_type(node, archive_type_proper, ctr_nodes)
                return False
            return True

        new_sources=filter(lambda x: is_source_file(x, control_sources), new_sources)

        # copy source node to build area, have to keep directory structure
        # Following logic will maintain the directory structure, e.g /bin/setup.py
        # try make a hardlink for the source files else do a full copy

        new_sources=env.CCopyAs(
                ['${{BUILD_DIR}}/_{2}/{0}/{1}'.format(target, env.Dir('${INSTALL_ROOT}').rel_path(n), archive_type_proper) for n in new_sources ],
                new_sources,
                CCOPY_LOGIC='hard-copy'
                )
        # really call the builder so everything is setup correctly
        # new sources are added along with control sources (files installed with PkgData for tar package)
        # to the target

        #function name is the output of correct builder type
        # example: if archive_type is 'tar', builder will be TarFile

        function_name="{0}File".format(archive_type_proper)
        getattr(env, function_name)(target, new_sources+control_sources,
                                    src_dir="$BUILD_DIR/_{0}/{1}".format(target, archive_type_proper),
                                    **kw)
    return archive_builder

def ArchivePackage_wrapper(env,target,sources,archive_type,**kw):
    # currently we assume all sources are Group values
    # will probally change this once we understand better

    target = common.make_list(target)
    sources= common.make_list(sources)

    if len(target) > 1:
        raise SCons.Errors.UserError('Only one target is allowed.')

    if str(target[0]).endswith('.' + archive_type):
         target=[env.Dir(".").File(target[0])]
    else:
         target=[env.Dir(".").File(target[0]+('.' + archive_type))]

    sources=[env.subst(s) for s in sources]

    glb.engine.add_preprocess_logic_queue(map_archive_builder(env, target[0], sources, archive_type,
                parts.errors.GetPartStackFrameInfo(), **kw))
    return target

# This is what we want to be setup in parts'''
from SCons.Script.SConscript import SConsEnvironment

SConsEnvironment.TarPackage = lambda env, target, sources, **kw: ArchivePackage_wrapper(env, target, sources, 'tar', **kw)
SConsEnvironment.ZipPackage = lambda env, target, sources, **kw: ArchivePackage_wrapper(env, target, sources, 'zip', **kw)
SConsEnvironment.TarGzPackage = lambda env, target, sources, **kw: ArchivePackage_wrapper(env, target, sources, 'tar.gz', **kw)
SConsEnvironment.TarBz2Package = lambda env, target, sources, **kw: ArchivePackage_wrapper(env, target, sources, 'tar.bz2', **kw)
SConsEnvironment.TgzPackage = lambda env, target, sources, **kw: ArchivePackage_wrapper(env, target, sources, 'tgz', **kw)
SConsEnvironment.Bz2Package = lambda env, target, sources, **kw: ArchivePackage_wrapper(env, target, sources, 'bz2', **kw)
SConsEnvironment.Tbz2Package = lambda env, target, sources, **kw: ArchivePackage_wrapper(env, target, sources, 'tbz2', **kw)

# vim: set et ts=4 sw=4 ai ft=python :

