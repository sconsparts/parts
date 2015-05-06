import SCons.Script
import parts.api as api
import parts.errors
import parts.common as common
import parts.glb as glb
import shutil, os,re
import operator,platform

rpm_reg="(\w+)\-([\d.]+)\-([\w.]+)\.(\w+)\.rpm"

def rpm_wrapper_mapper(env, target, sources, **kw):
    def rpm_builder():

        #############################################
        # getting all the sources
        new_sources, _ = env.GetFilesFromPackageGroups(target, sources)

        #############################################
        ## Sort files in to source group and to control group
        
        def spec(node):
            global spec_in
            if env.MetaTagValue(node, 'category', 'package')=='PKGDATA':
                if 'rpm' in env.MetaTagValue(node, 'types', 'package', ['rpm']):
                    if node.ID.endswith(".spec"):
                        spec_in=node
                    else:
                        env.CCopy('${{BUILD_DIR}}/SPECS/{0}'.format(target[0].name[:-4]),node)
                return False
            return True

        src=filter(spec,new_sources)
        grps=re.match(rpm_reg,target[0].name,re.IGNORECASE)
        
        target_name= grps.group(1)
        target_version= grps.group(2)
        target_release= grps.group(3)
        target_arch= grps.group(4)
        # make sure the TARGET_ARCH matched the value in the RPM file
        env['TARGET_ARCH']=target_arch
        
        filename = target_name+'-'+target_version


        #############################################
        ##create the source gz file
        #Replace source with the name and version  from the specfile for proper formatting of build of the tar.gz file
        #and building the rpm 
        try:
            spec_in
        except:
            api.output.error_msgf("No rpm spec file defined for RPM: {0}\n try adding a call to env.InstallPkgData('<yourRPM>.spec', packagetype = ['rpm'])",
            target[0].name,show_stack=False)
        # This depends statement seems to help address issues with getting symlink.linkto data        
        env.Depends(spec_in,src)
                        
        # copy the source files to be archived... this has to match how it would be installed
        # make note of meta values so we correctly copy to correct place in our fake root
        pkg_nodes=[]
        env['RPM_BUILD_ROOT']="${{BUILD_DIR}}/{0}".format(filename)
        for n in src:
            #get Package directory for node
            pk_type=env.MetaTagValue(n, 'category','package')
            pkg_dir="${{PACKAGE_{0}}}".format(pk_type)
            pkg_nodes.append(env.Entry('${{BUILD_DIR}}/{0}/{1}/{2}'.format(filename,pkg_dir,env.Dir(n.env['INSTALL_{0}'.format(pk_type)]).rel_path(n))))
            
        spec_file = env._rpmspec(
                            '${{BUILD_DIR}}/SPECS/{0}/{1}'.format(target[0].name[:-4],spec_in.name), 
                            spec_in,
                            NAME=target_name,
                            VERSION=target_version,
                            RELEASE=target_release,
                            PKG_FILES=pkg_nodes
                            )
            
        ret = env.CCopyAs(pkg_nodes, src, CCOPY_LOGIC='hard-copy')
        
        # archive the source file to be added to RPM needs to be in form of <target_name>-<target_version>.tar.gz
        d1=env.TarGzFile(('${{BUILD_DIR}}/_rpm/{0}/SOURCES/{1}.tar.gz').format(target[0].name[:-4],filename),ret)

        # copy the processed spec file to correct location for RPM build to work
        d2=env.CCopyAs(env.Dir('${{BUILD_DIR}}/_rpm/{0}/SPECS'.format(target[0].name[:-4])),env.Dir('${{BUILD_DIR}}/SPECS/{0}'.format(target[0].name[:-4])))
        env._rpm(target,d1+d2)

    return rpm_builder

    #Mapping for the target architecture with dictionary of known architectures
    #depending on the $TARGET_ARCH
    #the returned value is what RPM should like
def rpmarch(env,target_arch):
    arch_map_rpm = {}
    arch_map_rpm.update(glb.arch_map)
    arch_mapper = dict(env['PKG_ARCH_MAPPER'].items()+env.get('arch_mapper',{}).items())

    def implicit_rpm_mapping(target_arch):
        rpm_arch=None
        if not arch_mapper:
            rpm_arch = platform.machine()
        arch_map_rpm[target_arch]=rpm_arch
        return rpm_arch
    
    def explicit_rpm_mapping(target_arch):
        rpm_arch=None
        if arch_map_rpm.has_key(target_arch):
                 rpm_arch = arch_mapper[target_arch]
                 arch_map_rpm[target_arch]=rpm_arch
        return rpm_arch

    try:
        #explicit mapping: when the given architecture maps to arch_map_rpm for the system
        # it uses the corresponding value for target_arch
        # else if the key is not in arch_map_rpm (glb.arch_map), it maps to the new value
        if target_arch == arch_mapper[target_arch]:
            if arch_map_rpm.get(target_arch)==arch_mapper.get(target_arch): 
               new_target_arch = target_arch

        elif arch_map_rpm.has_key(target_arch):
             if arch_mapper.get(target_arch) is not None: 
                arch_map_rpm[target_arch]=explicit_rpm_mapping(target_arch)
                new_target_arch = arch_map_rpm[target_arch]

    except KeyError:
            #implicit mapping: when the given architecture is none,
            # the key maps to the platform system architecture
            arch_map_rpm[target_arch]=implicit_rpm_mapping(target_arch)
            new_target_arch = arch_map_rpm[target_arch]
    return new_target_arch


def RpmPackage_wrapper(_env, target, sources, **kw):
    # currently we assume all sources are Group values
    # will probally change this once we understand better
    # clone the KWS to the env to change the filename

    env= _env.Override(kw)
    
    # map arch to value the RPM will want to use
    env['TARGET_ARCH'] = rpmarch(env,env['TARGET_ARCH'])
    api.output.verbose_msgf(['rpm'],"mapping architecture to rpm value of: {0}",env['TARGET_ARCH'])
    
    # make node, now that TARGET_ARCH should be RPM friendly value 
    target = env.arg2nodes(target,env.fs.File)
    sources= common.make_list(sources) 

    if len(target) > 1:
        raise SCons.Errors.UserError('Only one target is allowed.')

    # give us the rpm name without the path on it
    fname = target[0].name

    #making sure we have .rpm on the end of the file name
    # We are also making the correct target path, this allows many different RPM
    # to be correct built without name conflicts
    # the finial value should like $build_dir/_rpm/<rpm_name>/<rpm_name>.rpm
    if str(fname).endswith('.rpm'):
        target=[env.Dir("_rpm/{0}".format(fname[:-4])).File(fname)]
    else:
        target=[env.Dir("_rpm/{0}".format(fname)).File(fname+".rpm")]
        
    # validate RPM name
    api.output.verbose_msgf(['rpm'],"validating string value of: {0}",target[0].name)
    grps=re.match(rpm_reg,target[0].name,re.IGNORECASE)
    if grps is None:
        api.output.error_msg("RPM target files must be in format of <name>-<version>-<release>.<arch>.rpm\n current format of value of target file is '{0}'".format(target[0].name))

    # subst all source values to get finial package group names
    sources=[env.subst(s) for s in sources]

    # delay real work till we have everything loaded
    glb.engine.add_preprocess_logic_queue(rpm_wrapper_mapper(env, target, sources, **kw))

    return target

api.register.add_variable('PKG_ARCH_MAPPER',{},'')

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

SConsEnvironment.RPMPackage=RpmPackage_wrapper
