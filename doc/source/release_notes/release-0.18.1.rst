***************
Release  0.18.1
***************
* Internal fix to add certain items that are exported to the internal list only once.
* some clean up of the code comments.
* Fix to testing logic in which would not scan and see variant directory correctly.
* update Pattern to not recurse into directories when the exclude patterns that would match the directory.
* patch to not allow information to be released by scons ( temporary fix to address a crash condition that can happen on rebuilds)
* Fix to allow the use of scons 4.7.0