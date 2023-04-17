***************
Release  0.17.5
***************

* Update a VerboseMsgf again with better fix to deal with no arguments
* Pattern will auto Ignore certain target source relationships for files under a .git directory to avoid false incremental rebuilds
* Add fix to RPMPackage() builder to not try to run_path items when PACKAGE_AUTO_RUNPATH is not set to True.
* Add top_level to CMake() builder. Set to True be default. Allow for lesser file tracking for CMake builds with can speed up over startup time.
* Cmake now accepts CCFlags option better. This may break you build as you might have to add new flags to supress error messages that did not show up before.
* Fixes to the toolsetting logic to address a case in which items are not found.

  * Added better verbose messageing to this logic
  
* Add some testing and fixes to address issues with the unit testing not:

  * Processing ``Test.Target`` values correctly if the value was a string type not a list object
  * Handing files extension for ``Test.Target`` inputs
