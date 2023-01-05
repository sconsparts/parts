***************
Release  0.17.0
***************

* Change CCopy builder that calls a script and uses the batch_key feature in SCons.
* Removed the options for hard-soft-copy, soft-hard-copy and soft-copy from the --copy commadline argument.
* Added a CCOPY_BATCH_KEY_MAX_COUNT variable to control the max size of a batch.
* A number of fixes to Symlink scanner.
* Internal fixes to nodes that are defined by Parts. Among these fixes was the removal of the import.jsn files.
* Some fixes to have Part process Directory target nodes better.
* Added a new api.register.add_method() function to better register functions with the Scons Environment() and Scons OverrideEnvironment().
* Add error check in recursive Pattern() logic to detect if Variant node value returned is being defined recursively by mistake.
* moved to ccopy.py to parts.core.builders.
* update a number of builders that do copy logic to define batch_key logic use in the new CCopy logic.
* SetRpath should not try to modify object files now.
* Internal function BottomLevelTargets and TopLevelTargets target refactored to work a magnitude faster.
* Adding a new ExtractFiles() builder (still a WIP) to help with some furture features.



Notes
=====

CCopy changes
-------------

The attempt here is to turn the copy logic into a script as this should allow SCons to scale better with -jN. 
The realtity is that helps a little, but not as much as desired. 
In certain cases it might slow the build down a little, which normally happens when builder has small batch sizes/
It is seen that when coping large amount of files that the build does speed up. 
This is seen in -J1 builds the most.

There is a CCOPY_BATCH_KEY_MAX_COUNT value that can be defined to control the max size of batch of files to copy.
The current default is 50 as that was found to be a good value overall. 
Certain cases might perform better with a smaller or larger number.
Having to large of a number can have very negative impact on the speed SCons can process the nodes.

The logic for coping files via hard-soft-copy, soft-hard-copy and soft-copy have been removed because the handling of the symlink node as first class objects would cause conflict with an incremental rebuild.


