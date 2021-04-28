Tool Chains

Part enhances the concept of the SCons tools by allowing the definition of the toolchains.
Currently, Scons which requires the user to write code or manual set the tools to be used in the Environment object.
If no tools are provided there is an internal magic tool called default which loads a set of tools based on the
system the user is running on. This does not allow the user much control, without having to write some custom code,
the ability to select different tools to be used for a given build.

With the addition of toolchains Part allows for:

* a more formal definition of a set of tools that are used to construct an environment
* a well-defined way to define the toolchain on the command line or environment.
* allow the use of different compilers, or adding library environments or unique builder API's needed in the build. 
  Ideally anything a SCons tool can be used for.
* the user to provide the exact requirement for a given build no matter how “picky” or flexible you want them to be.
