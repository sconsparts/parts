***************
Release  0.18.0
***************
* Added a ``InstallCMakeConfig()`` and ``SdkCMakeConfig()`` builder that will install the cmake config files. 
* Added ``X_RPM_OBSOLETES`` to the ``RpmPackage`` builder to allow for the setting of the Obsoletes tag.
* Added ``SKIP_RPATH`` variable that will prevent package builder from trying to process a files rpath. Add this value via MetaTag() to a node to prevent it from being processed.
* Added a new ``PkgConfigUninstall`` builder that will generate `-uninstalled.pc`file for a given `.pc` file.  
  pkg-config will prefer the `-uninstalled.pc` file over the installed `.pc` file forms making it easy to build against the uninstalled version of a package.
  This is useful for projects with other build systems, such as automake. 
  This allows the project to generate file for the finial package install location while having dependant projects to use the build locations.
  In general this will be call be the ``SDKPkgConfig`` builder or the ``DirectoryScanner`` scanner so direct usage is useful only for more advance cases
* Add to ``SDKPkgConfig`` a new argument of ``from_prefix`` and ``make_uninstall`` to control the generation of the uninstalled .pc file. 
  The ``SDKPkgConfig`` build will pass these arguments to the ``SDKPkgConfig`` builder. However it will not generate the `-uninstalled.pc` files at the install level.
  If from_prefix is None then the `-uninstalled.pc` will try to use the ``$PACKAGE_ROOT`` as the value to replace.
  If make_uninstall is set to True then the `-uninstalled.pc` file will be generated.
* Automake() builder
    * The argument ``prefix`` now by default tries to use the ``PACKAGE_ROOT`` environment variable as the prefix. If None, then the old behavior is used.
    * New environment variables:
        * **AUTO_MAKE_CONFIGURE_PREFIX** - The location to install to. Defaults to ``$PACKAGE_ROOT``.
        * **AUTO_MAKE_INSTALL_DESTDIR** - The location under the build directory to install to with "assumed" package root.
        * **AUTO_MAKE_DESTDIR_FLAG** - The flags we pass to the install command to tell it where to install to. Defaults to ``DESTDIR=${AUTO_MAKE_DESTDIR}`` given we have a defined prefix.
* Cmake() builder
    * Scanner now adds in generated .cmake files. 
    * The argument `prefix` now by default tries to use the ``PACKAGE_ROOT`` environment variable as the prefix. If None, then the old behavior is used.
    * New environment variables:
        * **CMAKE_INSTALL_PREFIX** - The location to install to. Defaults to ``$PACKAGE_ROOT``.
        * **CMAKE_INSTALL_DESTDIR** - The location under the build directory to install to with "assumed" package root.
        * **CMAKE_DESTDIR_FLAG** - The flags we pass to the install command to tell it where to install to. Defaults to ``DESTDIR=${CMAKE_INSTALL_DESTDIR}`` given we have a defined prefix.
* The load module logic now reports some error cases better
* Symlink handling of has been tweaked to better handling of getting context for signature vs builders that need the text context of the file it is linked to.
* updated range for rhel7 based dev toolset version that can be found
* clean up various sort() calls of certain builders.
* Added some more tests.

Notes
=====
.. py:function:: PkgConfigUninstall(target, source, from_prefix=None, to_prefix=None)

    Replaces the target with the uninstalled target for each source file.
    This is generally used to replace the prefix in the pkg-config file.
    Will normally be called by the SDK/Install functions and not directly.
      
    :param target: The target file(s) to process.
    :param source: The source file(s) to process.
    :param str from_prefix: The prefix to replace with the to_prefix.
    :param str to_prefix: The prefix to use in the prefix values.

    :return: A list of modified target file(s).
  