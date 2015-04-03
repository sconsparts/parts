
import section
import common
import core.util
import api.output


def resolve_dependents(manager,part):

    # see if we have called this one already
    if not part._has_section_phase_been_called('build','config'):
        
        # call the config section
        print "calling build.config on",part.Alias
        part._call_section('build','config')    
        
        for comp in part.Depends:
            # get the part for this case
            # and resolve it dependents
            comp.target=part.Env['TARGET_PLATFORM']
            tmp=comp.part
            
            resolve_dependents(manager,tmp)    
            #map full dependance information
            common.append_unique(part.FullDepends,tmp)
            common.extend_unique(part.FullDepends,tmp.FullDepends)

def call_emit(part):
    
    full_depends=part.FullDepends+[part]
    for p in full_depends:
        # map the depends data
        # this will also map stuff like rpath
        # and get full depends info
        for c in p.Depends:
            p.map_component_info(c)    
        # call the build sections
        p._call_section('build','emit')
        # map the rest of the aliases we need here
        p._map_alias()
    

def build_func(manager,target):
    ''' 
    manager is the part manger object that we can use to get more information
    or other parts objects
    target is the target we want to build
    '''
    plst=[]
    ## figure out if "target" means all parts or just a set of parts
    ## below we want for certain cases only the root parts as with subpart
    ## the need the parent to be read first, and as such the child might be
    ## defined
    if target.all:
        # ideally in this case we can just start calling stuff
        # however if we see that we can get top level part that would be the
        # best items to put in the list
        print "building 'all'"
        plst=manager.parts.values()
    elif target.alias:
        print "building alias",target.root_alias()
        plst=[manager._from_alias(target.root_alias())]
    elif target.name and target.version is None:
        print "building name no version"
        tmp=manager._alias_list(target.root_name())
        # for each alias we get the part that maps to it
        for a in tmp:
            plst.append(manager._from_alias(target.root_alias()))
    elif target.name and target.version:
        print "building name with version"
        tmp=manager._alias_list(target.name)
        # for each alias we get the part that maps to it
        vrange=version.version_range(target.version+".*")
        for a in tmp:
            # get the part from the alias
            ptmp=manager._from_alias(target.alias)
            #test to see if it is in range
            #if so add it
            if ptmp in vrange:
                plst.append(manager._from_alias(target.alias))
    
    
    for p in plst:
        if p is None:
            api.output.error_msg("Target \"%s\" was not found as a Part"%target.orginal_string)
        #Call config phase to get dependance information
        elif p._has_section_defined('build') == False:
            api.output.error_msg("Part does not have section build defined")
        
        # this will be recurisve and resolve all dependent parts as well
        resolve_dependents(manager,p)
            
        # at this point we know all the dependent parts
        # so we call the build.emit phase to find out what it will build
        print "calling build.emit on",p.Alias
        call_emit(p)
        
        # at this point we could try to force start the build of this target in SCons
        # just an option to consider later
    
    
    
    
    


bld_sec=section.section('build',build_func,['build'])
bld_sec.AddPhase('config',optional=True)
bld_sec.AddPhase('emit',optional=True)

api.register.add_section(bld_sec)
