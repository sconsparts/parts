# an enhanced Command function
# that also accepts target scanners

from typing import List, Dict, Any, Optional, Union
import parts.api as api
import SCons.Builder
import SCons.Scanner.Prog
import parts.core.scanners as scanners
# This is for type checking
from SCons.Node.FS import Dir
from SCons.Script.SConscript import SConsEnvironment


def CMake(env:SConsEnvironment, prefix:str="$PACKAGE_ROOT", cmake_dir:Union[str,Dir]=None, auto_scanner={}, ignore:List[str]=[], top_level:bool=True, hide_c_flags:bool=False, **kw):
    '''
        prefix - assumed install default location
        cmake_dir - directory containing cmakelist.txt in parent repo
        auto_scanner - scanner override to use finding finial output files from cmake
        ignore - list of files to ignore when defining the source files
        top_level - if true only track files in the top level directory ( can help with speed at cost if correctness )
        hide_c_flags - if true hide the CFLAGS from the cmake command line
    '''
    env_org = env
    env = env.Clone(**kw)
    build_dir : Dir = env.Dir("$BUILD_DIR/build")
    
    # The sandbox for the build install
    # we have three variables to help with this
    #
    # CMAKE_DESTDIR - the location under the build directory to install to
    # CMAKE_CONFIGURE_PREFIX - the location to install to based on default $PACKAGE_ROOT
    # CMAKE_INSTALL_DESTDIR - the location under the build directory to install to with "assumed" package root
    # CMAKE_DESTDIR_FLAG - The flags we pass to the install command to tell it where to install to
    if prefix:
        # if a prefix is provided (default) we expect to do a DESTDIR install
        env.SetDefault(CMAKE_CONFIGURE_PREFIX=env.Dir(prefix).abspath) # use Dir as this remove the '#' from the path    
        env.SetDefault(CMAKE_INSTALL_DESTDIR="${CMAKE_DESTDIR}${CMAKE_CONFIGURE_PREFIX}")
        env.SetDefault(CMAKE_DESTDIR_FLAG="DESTDIR=${CMAKE_DESTDIR}")
        
    else:
        # if it is not provided we have a messed up automake build and we will want to install in the
        # default build location 
        env.SetDefault(CMAKE_CONFIGURE_PREFIX="${CMAKE_DESTDIR}") # use Dir as this remove the '#' from the path
        env.SetDefault(CMAKE_INSTALL_DESTDIR="${CMAKE_DESTDIR}") 
        env.SetDefault(CMAKE_DESTDIR_FLAG="")

    cmake_scan_dir=env.subst("$CMAKE_INSTALL_DESTDIR")
    env_org.SetDefault(CMAKE_INSTALL_DESTDIR=cmake_scan_dir)
    
    env.SetDefault(CMAKE='cmake')
    env['RUNPATHS'] = r'${GENRUNPATHS("\\$$$$$$$$ORIGIN")}'

    
    cflags = '-DCMAKE_C_FLAGS="$CCFLAGS" -DCMAKE_CXX_FLAGS="$CCFLAGS" '
    if hide_c_flags:
        cflags=''

    env.SetDefault(_CMAKE_ARGS='\
        -DCMAKE_INSTALL_PREFIX=$CMAKE_CONFIGURE_PREFIX '
        '-DCMAKE_INSTALL_LIBDIR=lib '
        '-DCMAKE_INSTALL_BINDIR=bin '
        '-DCMAKE_BUILD_TYPE=Release '
        +cflags+
        '-DCMAKE_SHARED_LINKER_FLAGS="$LINKFLAGS $_RUNPATH $_ABSRPATHLINK" '
        '-DCMAKE_EXE_LINKER_FLAGS="$LINKFLAGS $_RUNPATH $_ABSRPATHLINK" '
        '-DCMAKE_CXX_COMPILER=$CXX '
        '-DCMAKE_C_COMPILER=$CC '
        '$CMAKE_ARGS'
                   )
    
    if 'cmakedir' in kw:
        cmake_dir = kw['cmakedir'] # for backwards compatibility
    if cmake_dir:
        cmake_file = "${CHECK_OUT_DIR}/" +  str(cmake_dir) + "/CMakeLists.txt"
    else:
        cmake_file = "${CHECK_OUT_DIR}/CMakeLists.txt"

    # generate the build files
    out = env.CCommand(
        [build_dir.File("Makefile")],
        [cmake_file],
        [
            # delete the directory as it can contains cached data
            SCons.Defaults.Delete(build_dir),
            # remake the directory as SCons thought it did this already
            SCons.Defaults.Mkdir(build_dir),
            # delete the directory we plan to install stuff into ..
            # as this is probally out of date ( contains bad files to scan)
            SCons.Defaults.Delete("$CMAKE_DESTDIR"),
            'cd ${TARGET.dir} ;'
            # CMAKE_PREFIX_PATH should replace this.. Have it as a fallback
            '${define_if("$PKG_CONFIG_PATH","PKG_CONFIG_PATH=")}${MAKEPATH("$PKG_CONFIG_PATH")} '
            '$CMAKE ${SOURCE.dir.abspath} $_CMAKE_ARGS'
        ],
        #source_scanner=scanners.NullScanner,
        target_scanner=scanners.NullScanner,
        source_scanner=scanners.DependsSdkScanner,
        # to help with debugging
        name="CMakeGenerate",
    )
    cmake_build_files = ["CMakeLists.txt"]

    # make sure this is a list
    if not isinstance(ignore, list):
        ignore = []

    if top_level:
        # track a lesser set.. which is probally ok as if CMake is being called this is probally
        #  only needed for support 
        src_files = env.Pattern(src_dir="${CHECK_OUT_DIR}", excludes=cmake_build_files+[".git/*"]+ignore, recursive=False).files()
    else:
        # track a lot of files
        src_files = env.Pattern(src_dir="${CHECK_OUT_DIR}", excludes=cmake_build_files+[".git/*"]+ignore).files()
    env.SetDefault(_CMAKE_MAKE_ARGS='VERBOSE=1\
        $(-j{jobs}$)'.format(jobs=env.GetOption('num_jobs'))
                   )

    ret = env.CCommand(
        [
            cmake_scan_dir,
        ],
        out + src_files,
        [
            "cd ${SOURCE.dir} ; $CMAKE --build . --config Release --target install -- $CMAKE_DESTDIR_FLAG $_CMAKE_MAKE_ARGS"
        ],
        source_scanner=scanners.NullScanner,
        target_factory=env.Dir,
        target_scanner=env.ScanDirectory(
            cmake_scan_dir,
            # Program scanner for getting libs
            #extra_scanner=SCons.Scanner.Prog.ProgramScanner(),
            **auto_scanner
        ),
        # to help with debugging
        name="CMakeDestDir",
    )

    # export the install location
    env.ExportItem("DESTDIR_PATH", env.Dir(cmake_scan_dir).abspath)
    return ret


# adding logic to Scons Environment object
api.register.add_method(CMake)

api.register.add_variable('CMAKE_DESTDIR', '${ABSPATH("$BUILD_DIR/destdir")}', 'Defines location to install bits from the CMake')
