
from typing import Optional,Dict
import os
import sys


build_context_files = set()

engine = None
rpter = None
pnodes = None
part_frame = []
_host_platform = None
builders = {}
env_cache = {}
# global object to add to parts call
parts_objs = {}
parts_objs_env = {}
known_concepts:Dict[str,str] = {}


# state object of what is being processed.
#part_being_processed = []

# known concepts based on section being defined
# maps a concept to section. a section can define
# many different concepts
known_concepts = {
    #'utest': 'utest',
    #'run_utest': 'utest',
    #'build': 'build'
}

processing_sections=False

# set of the part we know we want to build
buildable_part = set()
# set of alias we are targeting to be build as source
target_alias = set()
# set of parts we want to build as an SDK, given that it exists in the sdk directory
build_as_sdk = set()
# depends data we stored
depends_data = {}
# custom data mappers
mappers = {}
# these are the global functions we define to the SConstruct
globals = {}
# these are all the sections that have been defined
section_definitions = {}
# subst cache to help with speed up build
subst_cache = {}

# path to where Parts is installed
parts_path = os.path.abspath(os.path.split(__file__)[0])

# this is the path to the Sconstruct file
# this get reset to a better value
sconstruct_path = os.path.abspath(".")

############################## Platform Maps ################################

arch_map = {
    'ia32': 'x86',
    'x86': 'x86',
    'i386': 'x86',
    'i486': 'x86',
    'i586': 'x86',
    'i686': 'x86',
    'i86pc': 'x86',
    'x64': 'x86_64',
    'AMD64': 'x86_64',
    'amd64': 'x86_64',
    'em64t': 'x86_64',
    'EM64T': 'x86_64',
    'x86_64': 'x86_64',
    'IA64': 'ia64',
    'ia64': 'ia64',
    'k1om': 'k1om',
    'arm': 'arm',
    'arm64': 'arm64',
    'any': 'any',
    'noarch': 'noarch',
    'NOARCH': 'NOARCH'
}

os_map = {
    'android': 'android',
    'win32': 'win32',
    'win64': 'win32',
    'xp': 'win32',
    'vista': 'win32',
    'win7': 'win32',
    'windows': 'win32',
    'posix': 'posix',
    'linux': 'posix',
    'fedora': 'posix',
    'rhel': 'posix',
    'ubuntu': 'posix',
    'hp-ux': 'hp-ux',
    'os2': 'os2',
    'cygwin': 'cygwin',
    'suse': 'posix',
    'sles': 'posix',
    'sunos': 'sunos',
    'solaris': 'sunos',
    'darwin': 'darwin',
    'mac': 'darwin',
    'macos': 'darwin',
    'freebsd': 'freebsd',
    'any': 'any'
}
valid_arch = None
valid_os = None
valid_platform_re = None
