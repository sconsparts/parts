# an enhanced Command function
# that also accepts target scanners


import parts.api as api
import parts.node_helpers as node_helpers
import SCons.Builder
import SCons.Scanner.Prog
import scanners
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment


def CMake(env, destdir=None, cmakedir=None, auto_scanner={}, ignore=[], **kw):
    '''
        cmakedir - directory containing cmakelis.txt in parent repo
    '''

    env = env.Clone(**kw)
    build_dir = env.Dir("$BUILD_DIR/build")
    # The sandbox for the build install
    if destdir:
        env["CMAKE_DESTDIR"] = env.Dir(destdir).abspath
    cmake_install_dir = env.Dir("$CMAKE_DESTDIR")
    env.SetDefault(CMAKE='cmake')
    env['RUNPATHS'] = r'${GENRUNPATHS("\\$$$$$$$$ORIGIN")}'

    env.SetDefault(_CMAKE_ARGS='\
        -DCMAKE_INSTALL_PREFIX=$CMAKE_DESTDIR\
        ${define_if("$DESTDIR_PATH","-DCMAKE_PREFIX_PATH=\\"")}${MAKEPATH("$DESTDIR_PATH",";")}${define_if("$DESTDIR_PATH","\\"")}\
        -DCMAKE_INSTALL_LIBDIR=lib\
        -DCMAKE_INSTALL_BINDIR=bin\
        -DCMAKE_BUILD_TYPE=Release\
        -DCMAKE_SHARED_LINKER_FLAGS="$LINKFLAGS $_RUNPATH $_ABSRPATHLINK"\
        -DCMAKE_EXE_LINKER_FLAGS="$LINKFLAGS $_RUNPATH $_ABSRPATHLINK"\
        -DCMAKE_CXX_COMPILER=$CXX\
        -DCMAKE_C_COMPILER=$CC\
        $CMAKE_ARGS'
                   )

    cmake_file = "${CHECK_OUT_DIR}/" +  cmake_dir + "/CMakeLists.txt"
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
        source_scanner=scanners.null_scanner,
        target_scanner=scanners.depends_sdk_scanner
    )
    cmake_build_files = ["CMakeLists.txt"]
    
    # make sure this is a list
    if not isinstance(ignore, list):
        ignore = []

    src_files = env.Pattern(src_dir="${CHECK_OUT_DIR}", excludes=cmake_build_files+[".git/*"]+ignore).files()
    env.SetDefault(_CMAKE_MAKE_ARGS='VERBOSE=1\
        $(-j{jobs}$)'.format(jobs=env.GetOption('num_jobs'))
                   )

    ret = env.CCommand(
        [
            cmake_install_dir,
        ],
        out+src_files,
        [
            "cd ${SOURCE.dir} ; $CMAKE --build . --config Release --target install -- $_CMAKE_MAKE_ARGS"
        ],
        source_scanner=scanners.null_scanner,
        target_factory=env.Dir,
        target_scanner=env.ScanDirectory(
            cmake_install_dir,
            # Program scanner for getting libs
            extra_scanner=SCons.Scanner.Prog.ProgramScanner(),
            **auto_scanner
        ),
    )

    # export the install location
    env.ExportItem("DESTDIR_PATH", env.Dir("$CMAKE_DESTDIR").abspath)
    return ret


# adding logic to Scons Environment object
SConsEnvironment.CMake = CMake

api.register.add_variable('CMAKE_DESTDIR', '${ABSPATH("destdir")}', 'Defines location to install bits from the CMake')
