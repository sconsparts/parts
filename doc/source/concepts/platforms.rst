Platforms
---------

Parts adds to the SCons `PLATFORM` concept by adding the more formal 
SystemPlatform object.
These objects add concept of the a general OS and architecture.
These object allow better control for cross platform builds and
control over defining setting or action based on where
the build is happening.
The SystemPlatform object can be extended by the user to add new
values that are not defined as part of the install.
The SystemPlatform object is exposed to the user as via the Environment 
as either HOST_PLATFORM or TARGET_PLATFORM.

HOST_PLATFORM
^^^^^^^^^^^^^

This defines the system the user is building on. 
For convenance The SystemPlatform object will map the OS and architecture value to
the Environments variables HOST_OS and HOST_ARCH.

TARGET_PLATFORM
^^^^^^^^^^^^^^^

This defines the system being built for.
By default this is the same as the HOST_PLATFORM.
Can be set via the command via the command line via the --target-platform argument
