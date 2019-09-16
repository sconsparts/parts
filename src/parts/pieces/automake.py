# an enhanced Command function
# that also accepts target scanners
from __future__ import absolute_import, division, print_function

import parts.api as api
import SCons.Builder
import parts.node_helpers as node_helpers
import SCons.Scanner.Prog
import scanners
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment



def AutoMake(env, autoreconf="autoreconf", autoreconf_args="-if", configure="configure", prefix=None, configure_args=[],
             targets="all", top_level=True, copy_src=True, copy_top=False, auto_scanner={}, **kw):
    '''
    auto make general logic
    autoreconf- the autoreconf program to call. for some project they have hacky wrapper scripts
                that will call this or some other magic to make what should happen at this stage
                work.
    autoreconf_args-Default arguments to use for autoreconf. Some autoconf like project might have
                    special arguments to pass, or don't want any arguments passed.
    configure - The deafult configure program to call. Some configure like projects (-openssl-)
                have a slightly different script (Configure) that should called instead
    prefix    - If defined will use custom prefix and add DESTDIR to the make install
    configure_args - are extra args we need to pass to correctly configure the build
    top_level - We can rebuild build the configure and makefiles based on
                the *.am file defined. However various build may not generate
                all the Makefile. This causes false rebuilds, which we want to avoid.
                Top_level is true as it will ignore all the makefiles thare are subdirectories
                that we should be able to most ignore. Given we don't know about them SCons
                will not correctly rebuild them if they are manual deleted. This forces
                the user to do a change that would rebuild the top level makefile.
    copy_src -  Because autoreconf messes with the source directory
                we may want to copy the sources over to build area
                as the project may not have added the temp outputs to the
                SCM ignore files. This can cause false rebuilds and mess up
                the default update logic with git.
                We do this by default to be safe out of box. However there
                are some speed improments to avoid this step. 
    copy_top -  If copy_src is True, then True will copy over only toplevel level file/dir as nodes
                if False (Default) it do a recurise search of files and copy them as nodes
                This can be a function which will be called. it will be pass the (env,build_dir)
                env is the environment object and build_dir is the Dir node to copy all items under
                and returns a tuple of (build_files, source_files) Where
                build_files are the files we need as sources to make the finial makefile
                source_file any sources that are copied to the build_dir and would cause the make command to re-run
                the builder will make source files an explict prepresiqute for the finial expected generate buildfile
                to build correct
    '''


    env=env.Clone(**kw)
    # set up the install location for the auto make build
    # and custom prefix for build
    if prefix:
        # we have a custom prefix set. this mean we need to 
        # add DESTDIR to the automake install command
        # add DESTDIR to the based on the value of AUTO_MAKE_DESTDIR
        # as this will be the value we need to use as the base
        env.PrependUnique(AUTOMAKE_INSTALL_ARGS=["DESTDIR=$AUTO_MAKE_DESTDIR"])
        # update the CONFIGURE_PREFIX to use the custom prefix value
        # this value need to be a absolute path.. try to do the right thing
        env["CONFIGURE_PREFIX"] = env.Dir(prefix).abspath
        # the new location that we will find information is now in the form of
        # the AUTO_MAKE_DESTDIR plus the prefix value.
        env["AUTO_MAKE_INSTALL_DESTDIR"]="$AUTO_MAKE_DESTDIR$CONFIGURE_PREFIX"
        
        
    else:
        # use default logic. ideally this case does not need the use of 
        # DESTDIR which in generally need when the automake build uses configure
        # paths to hard code at compile time locations on disk.
        env["CONFIGURE_PREFIX"] = '$AUTO_MAKE_DESTDIR'
        env["AUTO_MAKE_INSTALL_DESTDIR"] = '$AUTO_MAKE_DESTDIR'

    # set up some variable for various paths we might need
    # generation of some paths
    checkout_path = env.Dir("$CHECK_OUT_DIR")
    prefix_len = len(checkout_path.ID)+1

    build_dir = env.Dir("$BUILD_DIR/build")
    rel_src_path = build_dir.rel_path(checkout_path)

    auto_conf_pattern = env.Pattern(src_dir="${CHECK_OUT_DIR}", includes=["*.ac"])
    auto_make_pattern = env.Pattern(src_dir="${CHECK_OUT_DIR}", includes=["*.am"])

    top_level_auto_conf_pattern = env.Pattern(src_dir="${CHECK_OUT_DIR}", includes=["*.ac"], recursive=False)
    top_level_auto_make_pattern = env.Pattern(src_dir="${CHECK_OUT_DIR}", includes=["*.am"], recursive=False)

    # This generates all the expected build files (*am -> Makefile, *.ac -> configure) that should generate
    # The set that is generate is an unknown however as this depends on how the configure was made.
    # We allow for only top level files to be tracked to help work around this in certain cases. This is control
    # this recursive arg on the pattern object
    auto_conf_buildfile = []
    if top_level:
        auto_conf_buildfile += [build_dir.File(node.ID[prefix_len:-3]) for node in top_level_auto_make_pattern.files()]
        if not auto_conf_buildfile:
            # the build might have a setup in which they don't have *.am files but only .in. at this point we just want
            # to assume that "Makefile" will be created
            auto_conf_buildfile += [build_dir.File("Makefile")]
        if copy_src:
            auto_conf_buildfile += [build_dir.File(node.ID[prefix_len:-3]) for node in top_level_auto_conf_pattern.files()]
        else:
            auto_conf_buildfile += [checkout_path.File(node.ID[prefix_len:-3]) for node in top_level_auto_conf_pattern.files()]

    else:
        auto_conf_buildfile += [build_dir.File(node.ID[prefix_len:-3]) for node in auto_make_pattern.files()]
        if not auto_conf_buildfile:
            # the build might have a setup in which they don't have *.am files but only .in. at this point we just want
            # to assume that "Makefile" will be created
            auto_conf_buildfile += [build_dir.File("Makefile")]
        if copy_src:
            auto_conf_buildfile += [build_dir.File(node.ID[prefix_len:-3]) for node in auto_conf_pattern.files()]
        else:
            auto_conf_buildfile += [checkout_path.File(node.ID[prefix_len:-3]) for node in auto_conf_pattern.files()]

    env["CONFIGURE_ARGS"] = configure_args
    # move this to some "defaults" location
    # probally need to change the _concat to a __env__.ABSDir from ABSDir
    env["ABSDir"] = lambda pathlist: [env.Dir(p).abspath for p in pathlist]
    env['_ABSCPPINCFLAGS'] = '$( ${_concat(INCPREFIX, CPPPATH, INCSUFFIX, __env__, ABSDir, TARGET, SOURCE)} $)'
    env['_ABSLIBDIRFLAGS'] = '$( ${_concat(LIBDIRPREFIX, LIBPATH, LIBDIRSUFFIX, __env__, ABSDir, TARGET, SOURCE)} $)'
    env["_CONFIGURE_ARGS"] = '--prefix=$CONFIGURE_PREFIX\
        ${define_if("$PKG_CONFIG_PATH","PKG_CONFIG_PATH=")}${MAKEPATH("$PKG_CONFIG_PATH")}\
        CC=$CC\
        CXX=$CXX\
        CPPFLAGS="$CCFLAGS $CPPFLAGS $_CPPDEFFLAGS $_ABSCPPINCFLAGS"\
        CFLAGS="$CFLAGS"\
        CXXFLAGS="$CXXFLAGS"'
        #LDFLAGS="$_ABSRPATH $_ABSLIBDIRFLAGS"'
    

    configure_cmds = []
    if copy_src:
        rel_src_path = "."

        # update action for autoreconf
        if autoreconf:
            configure_cmds.append(
                'cd ${{TARGET.dir}} && {0} {1}'.format(autoreconf, autoreconf_args)
            ),

        # Apply the correct copy logic for the source
        if callable(copy_top):
            depends, sources = copy_top(env,build_dir)
        else:
            if copy_top:
                # copy only item at the top level ( great for repos with Tons of nodes)
                # as this can slow everything down processing (and scanning for) these nodes.

                # copy build src files ( only the items found at the top level as *.ac or *.am files)
                depends = env.CCopy(
                    target=build_dir,
                    source=[top_level_auto_conf_pattern, top_level_auto_make_pattern]
                )
            else:
                # copy the build files
                depends = env.CCopy(
                    source=[auto_conf_pattern, auto_make_pattern],
                    target=build_dir
                )

            # copy source files
            files = env.Pattern(src_dir="${CHECK_OUT_DIR}", excludes=["*.ac", "*.am"],recursive=not copy_top)
            sources = env.CCopy(
                source=files,
                target=build_dir
            )
                
        # make the expected build file outputs (ie the MakeFiles, Configure, not the .am or .ac files)
        # to depend on the sources we copied over.
        env.Requires(auto_conf_buildfile, sources)
    else:
        if autoreconf:
            configure_cmds.append(
                'cd ${{NORMPATH("$CHECK_OUT_DIR")}} && {0} {1}'.format(autoreconf, autoreconf_args)
            ),

        depends = auto_conf_pattern.files()
        # these are file that will be messing up the "source" area
        # need to all the user to add to this set
        ignore_files = [
            ".git/*",
            "configure",
            "*.ac",
            "*.am",
            "*.in",
            "*.in~",
            "*.m4",            
            "compile",
            "config.guess",
            "config.sub",
            "depcomp",
            "install-sh",
            "ltmain.sh",
            "missing",
            "INSTALL",
            # this should be the default.. but might have negitive side effects
            "autom4te.cache/*",
            "config/*"
        ]
        sources = env.Pattern(src_dir="${CHECK_OUT_DIR}", excludes=ignore_files).files()

    configure_cmds.append('cd ${{TARGET.dir}} && ${{define_if("$PKG_CONFIG_PATH","PKG_CONFIG_PATH=")}}${{MAKEPATH("$PKG_CONFIG_PATH")}} {path}/{configure} $_CONFIGURE_ARGS $CONFIGURE_ARGS'.format(configure=configure,path=rel_src_path))

    # generate the makefiles
    build_files = env.CCommand(
        auto_conf_buildfile,
        depends,
        configure_cmds,
        source_scanner=scanners.null_scanner,
        target_scanner=scanners.depends_sdk_scanner
    )
    env['RUNPATHS'] = r'${GENRUNPATHS("\\$$\\$$$$$$$$ORIGIN")}'
    
    ret=env.CCommand(
        [
            "$AUTO_MAKE_INSTALL_DESTDIR",
        ],
        build_files+sources,
        # the -rpath-link is to get the correct paths for the binaries to link with the rpath usage of the makefile
        [
            'cd ${{SOURCE.dir}} ; make LDFLAGS="$_RUNPATH $_ABSRPATHLINK $_ABSLIBDIRFLAGS" {target} V=1\
            $(-j{jobs}$)'.format(target=targets, jobs=env.GetOption('num_jobs')),
            'cd ${SOURCE.dir} ; make install $AUTOMAKE_INSTALL_ARGS'
        ],
        target_factory=env.Dir,
        target_scanner=env.ScanDirectory(
            "$AUTO_MAKE_INSTALL_DESTDIR",
            # Program scanner for getting libs
            extra_scanner=SCons.Scanner.Prog.ProgramScanner(),
            **auto_scanner
        ),
        
    )

    # export the install location
    env.ExportItem("DESTDIR_PATH",env.Dir("$AUTO_MAKE_DESTDIR").abspath)
    return ret

# adding logic to Scons Enviroment object
SConsEnvironment.AutoMake = AutoMake

api.register.add_variable('AUTO_MAKE_DESTDIR', '${ABSPATH("destdir")}', 'Defines namespace for building a unit test')
