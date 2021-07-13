***************
Release  0.16.2
***************

* Add a InstallSystemBin and SdkSystemBin api functions.
* Added logic to the directoryscan scanner to look for values in sbin and map them to InstallSystemBin
* Add fix to packaging run path logic for rpms to fix run path for sbin objects
* Address issues with size change in dictionary during Environment csig generation that happens during -j based builds randomly
* Cleaned up some tests
* Updated range for finding gcc with devtools on rhel7 systems
* added support for aocc 3.0 compiler
* Fix crash when ScmGit branch argument is None
* removed old code for generating a sdk.part file and related exports that are not used
