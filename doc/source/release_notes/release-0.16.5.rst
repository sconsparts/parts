***************
Release  0.16.5
***************

* Fix load order of pieces with engine initialization to avoid certain load issues.
* Add a Meson builder.
  
.. note:: 
     Requires Patchelf on Linux as the tool will NULL parts of the elf headers on install.    This corrects RUN_PATH values on the output executable

* Remove color codes from the component logger and global logger for text only outputs
* Fix cache key when using allow_duplicates to address certain advanced cases in which the key would reproduce for different cases.
* Fix logic issue so a part only resolves to itself as a dependency, vs another part with the same name.
* Fix case when SCons would view a side effect node as not being built. 
  This caused a problem where a node that was dependent on this side effect would artificially rebuild, even though it was up to date
* Fix a race condition with package node sorting on highly parrel builds
* Improve loading logic to resolve to know exports better for Parts that call dynamic builders, such as CMake() or AutoMake().
* RPM spec file generator fix to address components that have files with spaces in the name.
* Internal fix to address change to use newer hash_signature() API in SCons
* Add EXTERN_GIT_PROTOCOL variable to better address how to pull from an "extern" repo hosted in git.
* Fix case of target mapping, where there are no properties defined in the target value
* Various spelling fixes to output messages
