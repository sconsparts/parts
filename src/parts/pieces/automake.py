# an enhanced Command function
# that also accepts target scanners


from pathlib import Path

import parts.api as api
import SCons.Builder
from parts.pieces.append_action import AppendFile
import SCons.Scanner.Prog
import SCons.Defaults
import parts.core.scanners as scanners


def AutoMake(env, autoreconf="autoreconf", autoreconf_args="-if", configure="configure", prefix:str="$PACKAGE_ROOT", configure_args=[],
             auto_configure_args=True, configure_post_actions=None, targets="all", install_targets="install", top_level=True,
             copy_src=True, copy_top=False, auto_scanner={}, copy_scm=True, skip_check=False, check_targets='check', **kw):
    '''
    auto make general logic
    autoreconf- the autoreconf program to call. for some project they have hackie wrapper scripts
                that will call this or some other magic to make what should happen at this stage
                work.
    autoreconf_args-Default arguments to use for autoreconf. Some autoconf like project might have
                    special arguments to pass, or don't want any arguments passed.
    configure - The default configure program to call. Some configure like projects (-openssl-)
                have a slightly different script (Configure) that should called instead
    prefix - If defined will use custom prefix and add DESTDIR to the make install, 
                if None it will use the default $AUTO_MAKE_DESTDIR and not add DESTDIR to the make install
    configure_args - are extra args we need to pass to correctly configure the build
    auto_configure_args - extra value to set various flags with what Parts is using. Certain automake like
                projects don't allow setting flags at the configure level. Defaults to True.
    configure_post_actions - In cases of configure like systems it often needed to add special
                actions to make sure everything work after the configure logic before the make command is called
    target    - the target to use with the main make command. Defaults to 'all'
    top_level - We can rebuild build the configure and makefile based on
                the *.am file defined. However various build may not generate
                all the Makefile. This causes false rebuilds, which we want to avoid.
                Top_level is true as it will ignore all the makefile there are subdirectories
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
                the builder will make source files an explicit prerequisite for the finial expected generate build file
                to build correct
    copy_scm - Copy the scm directory (currently this mean only .git) when coping the source over when copy_src is True.
                This takes extra time and space but may be needed if the automake tool query git for information which
                many project seem to do.
    '''
    env_org=env
    env = env.Clone(**kw)
    # set up the install location for the auto make build
    # and custom prefix for build

    # AUTO_MAKE_DESTDIR - the location under the build directory to install to
    # AUTO_MAKE_CONFIGURE_PREFIX - the location to install to based on default $PACKAGE_ROOT
    # AUTO_MAKE_INSTALL_DESTDIR - the location under the build directory to install to with "assumed" package root
    # AUTO_MAKE_DESTDIR_FLAG - The flags we pass to the install command to tell it where to install to
    if prefix:
        # if a prefix is provided (default) we expect to do a DESTDIR install
        env.SetDefault(AUTO_MAKE_CONFIGURE_PREFIX=env.Dir(prefix).abspath) # use Dir as this remove the '#' from the path    
        env.SetDefault(AUTO_MAKE_INSTALL_DESTDIR="${AUTO_MAKE_DESTDIR}${AUTO_MAKE_CONFIGURE_PREFIX}")
        env.SetDefault(AUTO_MAKE_DESTDIR_FLAG="DESTDIR=${AUTO_MAKE_DESTDIR}")
    else:
        # if it is not provided we have a messed up automake build and we will want to install in the
        # default build location 
        env.SetDefault(AUTO_MAKE_CONFIGURE_PREFIX=env.Dir("${AUTO_MAKE_DESTDIR}").abspath) # use Dir as this remove the '#' from the path
        env.SetDefault(AUTO_MAKE_INSTALL_DESTDIR="${AUTO_MAKE_DESTDIR}")
        env.SetDefault(AUTO_MAKE_DESTDIR_FLAG="")
    
    auto_scan_dir=env.subst("$AUTO_MAKE_INSTALL_DESTDIR")
    env_org.SetDefault(AUTO_MAKE_INSTALL_DESTDIR=auto_scan_dir)
    env['CONFIGURE_PREFIX'] = "$AUTO_MAKE_CONFIGURE_PREFIX" # backward compatibility
    

    env.PrependUnique(AUTO_MAKE_INSTALL_ARGS=[env["AUTO_MAKE_DESTDIR_FLAG"]])

    # set up some variable for various paths we might need
    # generation of some paths
    checkout_path = env.Dir("$CHECK_OUT_DIR")
    prefix_len = len(checkout_path.ID)+1
    build_dir = env.Dir("$AUTO_MAKE_BUILDDIR")
    rel_src_path = build_dir.rel_path(checkout_path)

    auto_conf_pattern = env.Pattern(src_dir="${CHECK_OUT_DIR}", includes=["*.ac", "configure.in"])
    auto_make_pattern = env.Pattern(src_dir="${CHECK_OUT_DIR}", includes=["*.am"])

    top_level_auto_conf_pattern = env.Pattern(src_dir="${CHECK_OUT_DIR}", includes=["*.ac", "configure.in"], recursive=False)
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

    #env['_ABSCPPINCFLAGS'] = '$( ${_concat(INCPREFIX, CPPPATH, INCSUFFIX, __env__, ABSDir, TARGET, SOURCE)} $)'
    #env['_ABSLIBDIRFLAGS'] = '$( ${_concat(LIBDIRPREFIX, LIBPATH, LIBDIRSUFFIX, __env__, ABSDir, TARGET, SOURCE)} $)'
    if auto_configure_args:
        env["_CONFIGURE_ARGS"] = '--prefix=$CONFIGURE_PREFIX\
            ${define_if("$PKG_CONFIG_PATH","PKG_CONFIG_PATH=")}${MAKEPATH("$PKG_CONFIG_PATH")}\
            CC="$CC"\
            CXX="$CXX"\
            CPPFLAGS="$CCFLAGS $CPPFLAGS $_CPPDEFFLAGS $_ABSCPPINCFLAGS"\
            CFLAGS="$CCFLAGS $CFLAGS"\
            LDFLAGS="$LINKFLAGS $_RUNPATH $_ABSRPATHLINK $_ABSLIBDIRFLAGS"\
            CXXFLAGS="$CXXFLAGS $CCFLAGS $CPPFLAGS"'
    else:
        env["_CONFIGURE_ARGS"] = ""

    configure_cmds = [
        # delete the make install area if we are rebuilding the
        # the makefile to avoid old files being added to the
        # scan.
        SCons.Defaults.Delete(build_dir),
        # remake the directory as SCons thought it did this already
        SCons.Defaults.Mkdir(build_dir),
        # delete the directory we plan to install stuff into ..
        # as this is probably out of date ( contains bad files to scan)
        SCons.Defaults.Delete("$AUTO_MAKE_DESTDIR"),
    ]
    scm_sources = []
    if copy_src:
        # need to this on how we can deal with the copy and remove the copied files
        # or do we just deal with possible bugs in some 3rd party builds???
        # worried that if we are coping it is probably messed up enough to be an issue here
        configure_cmds = [
            # delete the directory we plan to install stuff into ..
            # as this is probally out of date ( contains bad files to scan)
            SCons.Defaults.Delete("$AUTO_MAKE_DESTDIR"),
        ]
        rel_src_path = "."

        # update action for autoreconf
        if autoreconf:
            configure_cmds.append(
                f'cd {build_dir.path} && {autoreconf} {autoreconf_args}'
            ),

        # Apply the correct copy logic for the source
        if callable(copy_top):
            depends, sources = copy_top(env, build_dir)
        else:
            # what we normally want to skip
            exclude_srcs = ["*.ac", "*.am", "*.git/*", "configure.in"]
            if Path(env.subst("${CHECK_OUT_DIR}/configure.ac")).exists():
                # because some cases this is checked in and will be replaced with the configure.ac
                exclude_srcs += ["configure"]

            batch_key = hash("automake"), checkout_path

            if copy_top:
                # copy only item at the top level ( great for repos with Tons of nodes)
                # as this can slow everything down processing (and scanning for) these nodes.

                # copy build src files ( only the items found at the top level as *.ac or *.am files)
                depends = env.CCopy(
                    target=build_dir,
                    source=[top_level_auto_conf_pattern, top_level_auto_make_pattern]
                )
                # copy source files ( Pattern does not return Dir node at this time)
                files = env.Glob("${CHECK_OUT_DIR}/*", exclude=exclude_srcs)
                sources = env.CCopy(
                    source=files,
                    target=build_dir,
                    CCOPY_BATCH_KEY=batch_key
                )
            else:
                # copy the build files
                depends = env.CCopy(
                    source=[auto_conf_pattern, auto_make_pattern],
                    target=build_dir,
                    CCOPY_BATCH_KEY=batch_key
                )

                # do we need to copy git scm info as well?
                if copy_scm:
                    git_files = env.Pattern(src_dir="${CHECK_OUT_DIR}", includes=["*.git/*"], excludes=[".git/index"])
                    # need to treat ./git/index differently as it state changes and can cause false rebuilds
                    if git_files.files():
                        scm_sources = env.CCopy(
                            source=git_files,
                            target=build_dir,
                            CCOPY_BATCH_KEY=batch_key
                        )

                # copy source files
                files = env.Pattern(src_dir="${CHECK_OUT_DIR}", excludes=exclude_srcs)
                sources = env.CCopy(
                    source=files,
                    target=build_dir,
                    CCOPY_BATCH_KEY=batch_key
                )

        # make the expected build file outputs (ie the MakeFiles, Configure, not the .am or .ac files)
        # to depend on the sources we copied over.
        env.Requires(auto_conf_buildfile, sources+scm_sources)
    else:
        # this is the not copying source logic

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
            "config/*",
            "*/autom4te.cache",
            "*/config",
        ]+env.get("IGNORE_FILES", [])
        sources = env.Pattern(src_dir="${CHECK_OUT_DIR}", excludes=ignore_files).files()

    configure_cmds.append(
        f'cd {build_dir.path} && ${{define_if("$PKG_CONFIG_PATH","PKG_CONFIG_PATH=")}}${{MAKEPATH("$PKG_CONFIG_PATH")}} {rel_src_path}/{configure} $_CONFIGURE_ARGS $CONFIGURE_ARGS'
    )
    if configure_post_actions:
        configure_cmds.append(configure_post_actions)
    jobs = env.GetOption('num_jobs')
    # generate the makefile
    api.output.trace_msgf(
        ['automake.makefile.depends','automake.makefile','automake'],
        "target={target} source={source}",
        target=auto_conf_buildfile,
        source = depends+sources,
        )
    build_files = env.CCommand(
        auto_conf_buildfile,
        depends+sources,
        configure_cmds,
        #source_scanner=scanners.NullScanner,
        target_scanner=scanners.NullScanner,
        source_scanner=scanners.DependsSdkScanner,
        # to help with debugging
        name="AutoMakeConfigure",
    )
    env['RUNPATHS'] = r'${GENRUNPATHS("\\$$\\$$$$$$$$ORIGIN")}'

    ret = env.CCommand(
        [
            auto_scan_dir, 
        ],
        build_files+sources,
        # the -rpath-link is to get the correct paths for the binaries to link with the rpath usage of the makefile
        [
            f'cd {build_dir.path} ; make $_AUTOMAKE_BUILD_ARGS $AUTOMAKE_BUILD_ARGS {targets} $(-j{jobs}$)',
            f'cd {build_dir.path} ; make {install_targets} $AUTO_MAKE_INSTALL_ARGS'
        ],
        source_scanner=scanners.NullScanner,
        target_factory=env.Dir,
        target_scanner=env.ScanDirectory(
            auto_scan_dir,
            # Program scanner for getting libs
            #extra_scanner=SCons.Scanner.Prog.ProgramScanner(),
            **auto_scanner
        ),
        # to help with debugging
        name="AutoMakeDestDir",
    )

    skip_check = True
    if not skip_check:
        api.output.verbose_msg(["automake"], "Generating unit_test for '{name}' with make target {target}".format(
            name=env.PartName(), target=check_targets))
        # test target for standard make check from automake
        env.UnitTest(
            target="check",  # output file that we want to run
            # the source we need to "make" the target
            source=['$AUTO_MAKE_DESTDIR'],
            builder="CCommand",  # builder name to use to build the target from sources
            builder_kw=dict(
                action=[
                    AppendFile(
                        '$TARGET',
                        '#! /bin/bash\n' +
                        f'pushd {build_dir.abspath}\n' +
                        'set -e\n' +
                        'set -x\n' +
                        'export LD_LIBRARY_PATH=${__env__.Dir("$INSTALL_LIB").abspath}\n' +
                        'make $_AUTOMAKE_BUILD_ARGS $AUTOMAKE_BUILD_ARGS {target}\n'.format(target=check_targets) +
                        'set +x\n' +
                        "popd\n"),
                    SCons.Defaults.Chmod("$TARGET", 0o755)
                ],
            ),
        )
    else:
        api.output.verbose_msg(["automake"], "skipping unit_test generation for '{name}'".format(name=env.PartName()))

    # export the install location
    env.ExportItem("DESTDIR_PATH", env.Dir(auto_scan_dir).abspath)
    return ret


# adding logic to SCons Environment object
api.register.add_method(AutoMake)
api.register.add_variable('AUTO_MAKE_BUILDDIR', "$BUILD_DIR/build", 'Defines build directory for automake build')
api.register.add_variable('AUTO_MAKE_DESTDIR', '${ABSPATH("$BUILD_DIR/destdir")}', 'Defines install directory for automake build')
api.register.add_variable('_ABSCPPINCFLAGS', '$( ${_concat(INCPREFIX, CPPPATH, INCSUFFIX, __env__, ABSDir, TARGET, SOURCE)} $)', '')
api.register.add_variable(
    '_ABSLIBDIRFLAGS', '$( ${_concat(LIBDIRPREFIX, LIBPATH, LIBDIRSUFFIX, __env__, ABSDir, TARGET, SOURCE)} $)', '')
api.register.add_variable('_AUTOMAKE_BUILD_ARGS',
                          'LDFLAGS="$LINKFLAGS $MAKE_LINKFLAGS $_RUNPATH $_ABSRPATHLINK $_ABSLIBDIRFLAGS" V=1', '')
api.register.add_list_variable('AUTOMAKE_BUILD_ARGS', SCons.Util.CLVar(), '')
