
import parts.api as api
import parts.core.scanners as scanners
import SCons.Scanner
from SCons.Script.SConscript import SConsEnvironment

# We set buildtype=plain by default so SCons can have complete control over the
# build environment, otherwise there can be unpleasant surprises
def Meson(env, auto_scanner={}, setup_args : str = '--buildtype=plain', **kw):
    env['RUNPATHS'] = r'${GENRUNPATHS("\\$$$$$$$$ORIGIN")}'

    out_config = env.CCommand(
        "${BUILD_DIR}/build/build.ninja",
        "${CHECK_OUT_DIR}/meson.build",
        [
            SCons.Defaults.Delete("${TARGET.dir.abspath}"),
            SCons.Defaults.Mkdir("${TARGET.dir.abspath}"),
            'cd ${TARGET.dir}; '
            "${define_if('$PKG_CONFIG_PATH','PKG_CONFIG_PATH=')}${MAKEPATH('$PKG_CONFIG_PATH')} "
            f'CC=$CC \
            CXX=$CXX \
            CFLAGS="$CCFLAGS $CFLAGS $_CPPDEFFLAGS $_ABSCPPINCFLAGS" \
            CXXFLAGS="$CXXFLAGS $CCFLAGS $CPPFLAGS $_CPPDEFFLAGS $_ABSCPPINCFLAGS" \
            LDFLAGS="$LINKFLAGS $_RUNPATH $_ABSRPATHLINK -Wl,--enable-new-dtags" \
            meson setup {setup_args} --prefix=${{MESON_DESTDIR}} ${{TARGET.dir.abspath}} ${{SOURCE.dir.abspath}}',
            #'cd ${TARGET.dir.abspath}; '
            #' meson configure build'
        ],
        source_scanner=scanners.NullScanner,
        target_scanner=scanners.DependsSdkScanner
    )

    # the auto scan logic here it to address issues with rpath handing that cannot be controlled
    # in meson. Currently the build system zero out the RPATH section of the elf format. At the moment
    # this only effect the binary "exe" files not the .so files
    _auto_scanner={
        "InstallBin":dict(
            source=lambda node, env, default=None: [
                env.SetRPath(
                env.Pattern(src_dir=node.Dir("bin"), includes=env["INSTALL_BIN_PATTERN"]).files()+
                env.Pattern(src_dir=node.Dir("bin32"), includes=env["INSTALL_BIN_PATTERN"]).files()+
                env.Pattern(src_dir=node.Dir("bin64"), includes=env["INSTALL_BIN_PATTERN"]).files(),
                RPATH_TARGET_PREFIX="$BUILD_DIR/_meson_RUNPATH_",
                # hack
                RUNPATH_STR=env.subst(env.subst("${_RPATHSTR}")).replace("\\",""),
                )
            ]
        )
    }

    _auto_scanner.update(auto_scanner)
    jobs=env.GetOption('num_jobs')
    out_install = env.CCommand(
        "$MESON_DESTDIR",
        out_config,
        [
            'cd ${SOURCE.dir}; '
            f'meson compile --verbose $(-j{jobs}$); '
            'meson install' # this strip rpath
        ],
        target_factory=env.Dir,
        target_scanner=env.ScanDirectory(
            "$MESON_DESTDIR",
            # Program scanner for getting libs
            extra_scanner=SCons.Scanner.Prog.ProgramScanner(),
            **_auto_scanner
        ),
    )
    # export the install location
    env.ExportItem("DESTDIR_PATH", env.Dir("$MESON_DESTDIR").abspath)


# adding logic to SCons Environment object
api.register.add_method(Meson)

api.register.add_variable('MESON_DESTDIR', '${ABSPATH("$BUILD_DIR/destdir")}', '')
