Tools
-----

Tools in Parts have been enhanced to make it generally easier to setup and configure.
These enhancements include:

* being able to define different versions to be used
* being able to apply configuration based on the current version, host and target platform
* various infrastructure to find and setup the required environment to run a given tool.
* can be applied to a toolchain to load a given set in an SCons environment.

These enhancements make it easier to setup the required tools for native or cross build cases.
Any existing tools in SCons can be used as is, as long as there are not a Parts override for it.
