import SCons.Script
import parts.api as api
import parts.errors
import parts.common as common
import parts.glb as glb
import shutil
import tempfile
import os

MACRO_STARTS = ('%description', '%prep', '%check', '%build', '%install', '%clean', '%files')
def is_macro_header(line):
    return any(line.startswith(start) for start in MACRO_STARTS)

def add_install_content(env, file_contents):
    deflines = ['%install', 'rm -rf "%{buildroot}"',
                'mkdir -p %{buildroot}', 'cp -a * %{buildroot}']

    #add default install contents
    for line in deflines:
        file_contents.append(line)

def add_prep_content(env, file_contents,prefix):
    deflines = ['%install', 'setup -q']

    #add default install contents
    for line in deflines:
        file_contents.append(line)

def add_files_content(env, file_contents, pkg_files, prefix, idx=-1):
    # add all content in archive file
    defattrs = '%defattr(-,root,root,-)'

    files = []
    for f in pkg_files:
        repstr = env.subst('${RPM_BUILD_ROOT}').lstrip('#')
        files.append(f.ID.replace(repstr, ''))
        
    #TODO add like of MetaTag attributes mapping to RPM

    #if files section does not exist
    if idx == -1:
        file_contents.append('\n')
        file_contents.append('%files')
        file_contents.append(defattrs)
        for i in xrange(len(files)):
            file_contents.append('"{0}"'.format(files[i]))
    else:
        file_contents.insert(idx+1, defattrs)
        for i in xrange(len(files)):
            print '"{0}"'.format(files[i])
            file_contents.insert(idx+2+i, '"{0}"'.format(files[i]))


def rpm_spec(env, target, source):

    # these are set from rpm_package wrapper function
    target_name= env['NAME']
    target_version= env['VERSION']
    target_release= env['RELEASE']
    pkg_files = env['PKG_FILES']

    # open spec file
    with open(source[0].abspath, 'r') as file_obj:
        file_contents = file_obj.read().split('\n')

    # If BuildArch exists in specfile, delete the line
    # It will take host architecture as the build architecture by default
    file_contents = filter(lambda x : not x.startswith('BuildArch') ,
                           file_contents)

    # override some value to match name of out rpm files.
    found_install = False
    found_files = False
    found_prep = False
    
    #default rpm prefix value
    prefix = '/usr'
    
    # make this all the api.output...
    print "Overriding the spec file values for name, version, release"
    i=0
    #tmp set to detect duplicates of values that should only be defined once
    tmp=set(('name', 'version', 'release'))


    while i < len(file_contents): 

        if file_contents[i].startswith('Name'):
            file_contents[i]='Name:'+target_name
            try:
                tmp.remove('name')
            except KeyError:
               pass

        elif file_contents[i].startswith('Version'):
            file_contents[i] = 'Version:'+target_version            
            try:
                tmp.remove('version')
            except KeyError:
               pass
               
        elif file_contents[i].startswith('Prefix'):
            prefix=file_contents[i].split(":")[1].strip()


        elif file_contents[i].startswith('Release'):
            file_contents[i] = 'Release:'+target_release
            try:
                tmp.remove('release')
            except KeyError:
               pass

        elif file_contents[i].startswith('%install'):
            found_install = True
            
        elif file_contents[i].startswith('%prep'):
            found_prep = True

        #add file contents that will be installed in rpm
        elif file_contents[i].startswith('%files'):
            found_files = True   
            add_files_content(env, file_contents, pkg_files,prefix, i)
         
        i+=1
    
    #add sections if they do not exist
    if not found_install:
        add_install_content(env, file_contents)
        
    if not found_prep:
        add_prep_content(env, file_contents,prefix)

    if not found_files:
        add_files_content(env, file_contents, pkg_files,prefix)
        

    if tmp:
        api.output.warning_msg("Did not find keys value in spec file for {0}".format(", ".join(tmp)))
        
    #If BuildArch exists in specfile, delete the line
    # It will take host architecture as the build architecture by default
    file_contents= "\n".join(file_contents)+'\n'
    with open(target[0].abspath, 'wb') as out_file:
        out_file.write(file_contents)

    
rpmspec_action = SCons.Action.Action(rpm_spec)

api.register.add_builder('_rpmspec',SCons.Builder.Builder(
                    action = rpmspec_action,
                    source_factory = SCons.Node.FS.File,
                    target_factory = SCons.Node.FS.File
                    ))
