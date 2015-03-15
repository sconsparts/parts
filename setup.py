import sys,os
sys.path.append('./parts') 
import parts_version
#import distutils.file_util
#from distutils.command.install import install
#
#class custom_install(install):
#    def run(self):
#        self.uninstall = os.path.join(self.install_scripts, "%s_uninstall.py" % self.distribution.get_name())
#        
#        if os.path.exists(self.uninstall):
#            print "Uninstalling previous version"
#            if self.dry_run:
#                os.system("python %s -n" % self.uninstall)
#            else:
#                os.system("python %s" % self.uninstall)
#        
#        keep_record = True
#        if not self.record:
#            self.record = "install_record.txt"
#            keep_record = False
#        
#        self.force = 1
#        install.run(self)
#        
#        if not self.dry_run:
#            self._generate_uninstall()
#        
#        if not keep_record:
#            print "Removing unwanted record %s" % self.record
#            if not self.dry_run: os.remove(self.record)
#            self.record = None
#    
#    def _generate_uninstall(self):
#        print "Generating uninstall script in %s" % self.uninstall
#        out = open(self.uninstall, 'w')
#        out.write("#!/usr/bin/env python\n")
#        out.write("import os, sys\n\n")
#        out.write("files = [\n")
#        fin = open(self.record, 'r')
#        for line in fin:
#            line = line.strip();
#            line = line.replace('\\', "\\\\");
#            out.write("'%s',\n" % line)
#        
#        fin.close()
#        out.write("__file__\n")
#        out.write("]\n\n")
#        out.write("dry_run = False\n")
#        out.write("for arg in sys.argv:\n")
#        out.write("\tif arg == '-n':\n")
#        out.write("\t\tdry_run = True\n\n")
#        
#        out.write("for f in files:\n")
#        out.write("\tif os.path.exists(f):\n")
#        out.write("\t\tprint \"Removing %s\" % f\n")
#        out.write("\t\tif not dry_run: os.remove(f)\n")
#        
#        out.write("\tf = f + 'c'\n")
#        out.write("\tif os.path.exists(f):\n")
#        out.write("\t\tprint \"Removing %s\" % f\n")
#        out.write("\t\tif not dry_run: os.remove(f)\n")
#        
#        out.write("\tdir = os.path.dirname(f)\n")
#        out.write("\ttry:\n")
#        out.write("\t\twhile not dry_run:\n")
#        out.write("\t\t\tos.rmdir(dir)\n")
#        out.write("\t\t\tprint \"Removing %s\" % dir\n")
#        out.write("\t\t\tdir = os.path.dirname(dir)\n")
#        out.write("\texcept OSError:\n")
#        out.write("\t\tpass\n")
#        out.close()

def get_packages(path):
    ret=[]
    for d in os.listdir(path):
        np=os.path.join(path,d)
        if os.path.isdir(np) and d !='.svn':
            tmp=np.replace('/','.')[2:]
            tmp=tmp.replace('\\','.')            
            ret.append(tmp)
            tmp= get_packages(np)
            if tmp!=[]:
                ret.extend(tmp)
    return ret

def get_data_files(root,path,installpath):
    ret=[]
    files=[]
    if os.path.exists(path) == False:
        return ret
    pth=os.path.join(root,installpath)
    for d in os.listdir(path):
        np=os.path.join(path,d)
        if os.path.isdir(np) and d.endswith('.svn')==False:
            tmp= get_data_files(root,np,os.path.join(installpath,d))
            if tmp!=[]:
                ret.extend(tmp)
        elif os.path.isfile(np) and d.endswith('.py'):
            files.append(np)
    if files != []:
        ret.append( (pth,files) )
    return ret

def get_package_data(path,root):
    ret=[]
    files=[]
    
    # might not exist...
    if os.path.exists(path) == False:
        return ret
    
    for d in os.listdir(path):
        np=os.path.join(path,d)
        pkg_file=os.path.join(root,d)
        if os.path.isdir(np) and d.endswith('.svn')==False:
            tmp= get_package_data(np,pkg_file)
            if tmp!=[]:
                ret.extend(tmp)
        elif os.path.isfile(np) and d.endswith('.py'):
            tmp=pkg_file.replace('\\','/')  
            files.append(tmp)
    
    ret += files 
    return ret

pk_data=get_package_data('parts-site','')
# if the packaging of this parts distro has not "special" data to install
# we don't want to add the parts.parts-site directory package
# doing this mean the package_data will be ignored
if pk_data:
    pk_package=['parts.parts-site']
else:
    pk_package=[]
    
from distutils.core import setup
#try:
#    import py2exe
#except:
#    print "py2exe not found"

setup(name="parts",
        description="Extension module to SCons build system",
        author="Jason Kenny",
        author_email="jason.l.kenny@intel.com",
        version=parts_version._PARTS_VERSION,
        packages=['parts']+get_packages('./parts')+pk_package,
        scripts=['parts/parts.bat','parts/parts'],
        #cmdclass={'install':custom_install},
        package_dir={'parts.parts-site':'parts-site'},
        package_data={
                'parts.parts-site': pk_data,
                },
        data_files = [("", ["license.txt"])],
        url="http://parts.tigris.org/",
        license="MIT"
        #console=['main.py']
        )

# setup(name="parts_util",
#        description="Utility API for Parts (extension module to SCons build system)",
#        author="Andrey Kryachko, Jason Kenny",
#        author_email="andrey.kryachko@intel.com, jason.l.kenny@intel.com",
#        version=parts_version._PARTS_VERSION,
#        packages=['parts_util']+get_packages('./parts_util'),
#        # NB: We do not install _parts_util_setup_.py because it is needed only when
#        # scripts are invoked from local instance of Parts.
 #       scripts=[
 #           'scripts/parts_dump_cache.py',
 #           'scripts/parts_dump_dependency.py',
 #           'scripts/parts_process_nodes.py'],
 #       cmdclass={'install':custom_install}
 #       )
