# an enhanced Command function
# that also accepts target scanners


from pathlib import Path

import parts.api as api
import SCons.Builder
import parts.node_helpers as node_helpers
import SCons.Scanner.Prog
import SCons.Defaults
import scanners
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment


def AutoMake(env, autoreconf="autoreconf", autoreconf_args="-if", configure="configure", prefix=None, configure_args=[],
             auto_configure_args=True, configure_post_actions=None, targets="all", install_targets="install", top_level=True,
             copy_src=True, copy_top=False, auto_scanner={}, copy_scm=True, **kw):
    '''
    auto make general logic
    autoreconf- the autoreconf program to call. for some project they have hackie wrapper scripts
                that will call this or some other magic to make what should happen at this stage
                work.
    autoreconf_args-Default arguments to use for autoreconf. Some autoconf like project might have
                    special arguments to pass, or don't want any arguments passed.
    configure - The deafult configure program to call. Some configure like projects (-openssl-)
                have a slightly different script (Configure) that should called instead
    prefix    - If defined will use custom prefix and add DESTDIR to the make install
    configure_args - are extra args we need to pass to correctly configure the build
    auto_configure_args - extra value to set various flags with what Parts is using. Certain automake like
                projects don't allow setting flags at the configure level. Defaults to True.
    configure_post_actions - In cases of configure like systems it often needed to add special
                actions to make sure everthing work after the configure logic before the make command is called
    target    - the target to use with the main make command. Defaults to 'all'
    top_level - We can rebuild build the configure and makefiles based on
                the *.am file defined. However various build may not generate
                all the Makefile. This causes false rebuilds, which we want to avoid.
                Top_level is true as it will ignore all the makefiles there are subdirectories
                that we should be able to most ignore. Given we don't know about them SCons
                will not correctly rebuild them if they are manual deleted. This forces
                the user to do a change that would rebuild the top level makefile.
    copy_src -  Because autoreconf messes with the source directory
                we may want to copy the sources over to build area
                as the project may not have added the temp outputs to the
                SCM ignore files. This can cause false rebuilds and mess up
                the default update logic with git.
                We do this by default to be safe out of box. However there
                are some speed improvements to avoid this step.
    copy_top -  If copy_src is True, then True will copy over only toplevel level file/dir as nodes
                if False (Default) it do a recursive search of files and copy them as nodes
                This can be a function which will be called. it will be pass the (env,build_dir)
                env is the environment object and build_dir is the Dir node to copy all items under
                and returns a tuple of (build_files, source_files) Where
                build_files are the files we need as sources to make the finial makefile
                source_file any sources that are copied to the build_dir and would cause the make command to re-run
                the builder will make source files an explicit prepresiqute for the finial expected generate buildfile
                to build correct
    copy_scm - Copy the scm directory (currently this mean only .git) when coping the source over when copy_src is True.
                This takes extra time and space but may be needed if the automake tool query git for information which
                many project seem to do.
    '''

    env = env.Clone(**kw)
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
        env["AUTO_MAKE_INSTALL_DESTDIR"] = "$AUTO_MAKE_DESTDIR$CONFIGURE_PREFIX"

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
    env.SetDefault(AUTOMAKE_BUILD_ARGS=SCons.Util.CLVar(""))
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

    env['_ABSCPPINCFLAGS'] = '$( ${_concat(INCPREFIX, CPPPATH, INCSUFFIX, __env__, ABSDir, TARGET, SOURCE)} $)'
    env['_ABSLIBDIRFLAGS'] = '$( ${_concat(LIBDIRPREFIX, LIBPATH, LIBDIRSUFFIX, __env__, ABSDir, TARGET, SOURCE)} $)'
    if auto_configure_args:
        env["_CONFIGURE_ARGS"] = '--prefix=$CONFIGURE_PREFIX\
            ${define_if("$PKG_CONFIG_PATH","PKG_CONFIG_PATH=")}${MAKEPATH("$PKG_CONFIG_PATH")}\
            CC="$CC"\
            CXX="$CXX"\
            CPPFLAGS="$CCFLAGS $CPPFLAGS $_CPPDEFFLAGS $_ABSCPPINCFLAGS"\
            CFLAGS="$CFLAGS"\
            LDFLAGS="$LINKFLAGS $_RUNPATH $_ABSRPATHLINK $_ABSLIBDIRFLAGS"\
            CXXFLAGS="$CXXFLAGS $CCFLAGS $CPPFLAGS"'
    else:
        env["_CONFIGURE_ARGS"] = ""

    configure_cmds = [
        # delete the make install area if we are rebuilding the
        # the makefiles to avoid old files being added to the
        # scan.
        SCons.Defaults.Delete(build_dir),
        # remake the directory as SCons thought it did this already
        SCons.Defaults.Mkdir(build_dir),
        # delete the directory we plan to install stuff into ..
        # as this is probally out of date ( contains bad files to scan)
        SCons.Defaults.Delete("$AUTO_MAKE_DESTDIR"),
    ]
    scm_sources = []
    if copy_src:
        # need to this on how we can deal with the copy and remove the copied files
        # or do we just deal with possible bugs in some 3rd party builds???
        # worried that if we are coping it is probally messed up enough to be an issue here
        configure_cmds = [
            # delete the directory we plan to install stuff into ..
            # as this is probally out of date ( contains bad files to scan)
            SCons.Defaults.Delete("$AUTO_MAKE_DESTDIR"),
        ]
        rel_src_path = "."

        # update action for autoreconf
        if autoreconf:
            configure_cmds.append(
                'cd ${{TARGET.dir}} && {0} {1}'.format(autoreconf, autoreconf_args)
            ),

        # Apply the correct copy logic for the source
        if callable(copy_top):
            depends, sources = copy_top(env, build_dir)
        else:
            if copy_top:
                # copy only item at the top level ( great for repos with Tons of nodes)
                # as this can slow everything down processing (and scanning for) these nodes.

                # copy build src files ( only the items found at the top level as *.ac or *.am files)
                depends = env.CCopy(
                    target=build_dir,
                    source=[top_level_auto_conf_pattern, top_level_auto_make_pattern]
                )
                # copy source files ( Pattern does not return Dir node at this time)
                files = env.Glob("${CHECK_OUT_DIR}/*", exclude=["*.ac", "*.am"])
                sources = env.CCopy(
                    source=files,
                    target=build_dir
                )
            else:
                # copy the build files
                depends = env.CCopy(
                    source=[auto_conf_pattern, auto_make_pattern],
                    target=build_dir
                )

                if copy_scm:
                    git_files = env.Pattern(src_dir="${CHECK_OUT_DIR}", includes=["*.git/*"], excludes=[".git/index"])
                    # need to treat ./git/index differently as it state changes and can cause false rebuilds
                    if git_files.files():
                        git_index = env.File("${CHECK_OUT_DIR}/.git/index")
                        scm_sources = env.CCopy(
                            source=git_files,
                            target=build_dir
                        )
                        #env.AddPostAction(scm_sources[-1], env.Action(SCons.Defaults.Copy("$BUILD_DIR/build/.git/index",git_index.ID)))

                # copy source files
                files = env.Pattern(src_dir="${CHECK_OUT_DIR}", excludes=["*.ac", "*.am", "*.git/*"])
                sources = env.CCopy(
                    source=files,
                    target=build_dir
                )

        # make the expected build file outputs (ie the MakeFiles, Configure, not the .am or .ac files)
        # to depend on the sources we copied over.
        env.Requires(auto_conf_buildfile, sources+scm_sources)
    else:
        if autoreconf:
            configure_cmds.append(
                'cd ${{NORMPATH("$CHECK_OUT_DIR")}} && {0} {1}'.format(autoreconf, autoreconf_args)
            ),

        depends = auto_conf_pattern.files()
        # these are file that will be messing up the "source" area
        # need to allow the user to add to this set
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
            # this should be the default.. but might have negative side effects
            "autom4te.cache/*",
            "config/*"
        ]+env.get("IGNORE_FILES", [])
        sources = env.Pattern(src_dir="${CHECK_OUT_DIR}", excludes=ignore_files).files()

    configure_cmds.append(
        'cd ${{TARGET.dir}} && ${{define_if("$PKG_CONFIG_PATH","PKG_CONFIG_PATH=")}}${{MAKEPATH("$PKG_CONFIG_PATH")}} {path}/{configure} $_CONFIGURE_ARGS $CONFIGURE_ARGS'.format(configure=configure, path=rel_src_path))
    if configure_post_actions:
        configure_cmds.append(configure_post_actions)

    # generate the makefiles
    build_files = env.CCommand(
        auto_conf_buildfile,
        depends,
        configure_cmds,
        source_scanner=scanners.null_scanner,
        target_scanner=scanners.depends_sdk_scanner
    )
    env['RUNPATHS'] = r'${GENRUNPATHS("\\$$\\$$$$$$$$ORIGIN")}'
    env.SetDefault(_AUTOMAKE_BUILD_ARGS=SCons.Util.CLVar('LDFLAGS="$LINKFLAGS $_RUNPATH $_ABSRPATHLINK $_ABSLIBDIRFLAGS" V=1'))
    ret = env.CCommand(
        [
            "$AUTO_MAKE_INSTALL_DESTDIR",
        ],
        build_files+sources,
        # the -rpath-link is to get the correct paths for the binaries to link with the rpath usage of the makefile
        [
            'cd ${{SOURCE.dir}} ; make $_AUTOMAKE_BUILD_ARGS $AUTOMAKE_BUILD_ARGS {target} \
            $(-j{jobs}$)'.format(target=targets, jobs=env.GetOption('num_jobs')),
            'cd ${{SOURCE.dir}} ; make {install} $AUTOMAKE_INSTALL_ARGS'.format(install=install_targets)
        ],
        source_scanner=scanners.null_scanner,
        target_factory=env.Dir,
        target_scanner=env.ScanDirectory(
            "$AUTO_MAKE_INSTALL_DESTDIR",
            # Program scanner for getting libs
            extra_scanner=SCons.Scanner.Prog.ProgramScanner(),
            **auto_scanner
        ),

    )

    # export the install location
    env.ExportItem("DESTDIR_PATH", env.Dir("$AUTO_MAKE_DESTDIR").abspath)
    return ret


# adding logic to Scons Enviroment object
SConsEnvironment.AutoMake = AutoMake

api.register.add_variable('AUTO_MAKE_DESTDIR', '${ABSPATH("destdir")}', 'Defines namespace for building a unit test')
