***************
Release  0.16.0
***************

* Add new format syntax decorators to allow for future functionality and general startup speed up.
  
  * build section added.
  * unit_test section added to replace the UnitTest() builder.

* Changed logic of REQ items to be defined as internal=True instead of internal=False.
  
  * add COMPAT_REQ_INTERNAL variable that can be define to True to allow old behavior for all or selected set of Parts
  * Fix a number of builders in Parts to force use of a NullScanner to avoid scanning of global exertions files to improve build speed up

* VCS->SCM change. Allow objects and CLI options that had vcs in them are now changed to scm. Old code will work. However scm is the preferred form.
* New **extern** argument for the Part() call added to allow definition of a SCM object to get part/build files to define a given component
* `env.Part(...)` is not preferred anymore for defining a subparts. preferred form is to now just say `Part(...)`.
* Change logic to allow SRC_DIR to point to location of the checkout source when the Part file is defined out of the source repo.
* Change logic to allow PART_DIR always point to location where the Part file is defined.
* various fixes to help with certain cases in which a target to an part name or alias did not resolve correctly
* Add slots to requirements to reduce memory usage
* Drop support for python35
* AutoMake variables _ABSCPPINCFLAGS _ABSLIBDIRFLAGS _AUTOMAKE_BUILD_ARGS AUTOMAKE_BUILD_ARGS are define globally
* Fix regular expression to allow '+' in file names [`PR #64 <https://bitbucket.org/sconsparts/parts/pull-requests/64>`_]
* Add SdkSource InstallSource [`PR #63 <https://bitbucket.org/sconsparts/parts/pull-requests/63>`_]
* Add SDK_INCLUDE_PATTERN for adding include files to rpms [`PR #62 <https://bitbucket.org/sconsparts/parts/pull-requests/62>`_]
* Fix missing check in default_mappings before update [`PR #61 <https://bitbucket.org/sconsparts/parts/pull-requests/61>`_]
* Add cmakedir to CMake builder to allow defining location of CMakeList when not in top level directory [`PR #60 <https://bitbucket.org/sconsparts/parts/pull-requests/60>`_]
* CMAKE_DESTDIR and AUTOMAKE_DESTDIR fix to work out of box correctly.
* gcc and gxx tool updated to support rhel8 toolset directory changes from devtools layout
* Error and warning message now print an more interesting source points.
* Started documentation rewrite.


Notes
=====

The Vcs to SCM change
---------------------

There is a backward compatible change of vcs to scm within Parts API and CLI options. 
Effort has been made to make sure existing build files using the "vcs" forms will continue to work.
The change to motivated because of a large confusion on what vcs means. 
It stands for "Version Control System", however today most people under this as SCM (Source Code Management).
Going forward the use of scm will be preferred over the use of vcs. 
The obvious change that will be seen is the _vcs will not be used, but instead of _scm will be used as the default CHECK_OUT_ROOT value used by Parts.
Part() will prefer the use of scm_type instead of vcs_type and CLI options have been changed to have the scm form.


New File Format
---------------

Parts now support a slightly change file format that uses python declarator to allow for future functionality as well as speed up of full and partial builds.
The exposing of the build and unit testing section externally to the user is in the current drop. 
The design is being tweaked to allow any user to define or add custom section types to help solve different build domains.
Each section has one or more phases that can be defined as function with a certain name.
Each function is registered and called later given that the item is in the defined dependency tree of the build target.
A special function called ApplyIf() can be called to control is the function should be applied or not based on various conditions, 
such as build host, compiler or some other user condition.
The general form of phase look like:

.. code-block:: python

    @section_type
    def phase(...):
        ...

For example the build section can define "config" or "source" section.

.. code-block:: python

    # only defined when building for win32
    @build.ApplyIf(env['TARGET_OS']=='win32')
    def config(env):
        env.Append(CPPDEFINES= ['WINDOW_OS'])
    
    # always defined   
    @build
    def config(env):
        env.Append(CPPDEFINES= ['ALWAYS_DEFINED'])

    @build
    def source(env):
        cpp_files=['print_msg.c']
        env.InstallTarget(
            env.SharedLibrary('print_msg','print_msg.c')
        )
        env.SdkInclude(['print_msg.h'])

Different phases can define different inputs to be provided for call back function. 
As an example with the unit_test section a test context is passed in.

.. code-block:: python

    # build a simple test
    @unit_test.Group("test1")
    def run(env, test):
        test.Sources = Pattern(src_dir='test1', includes = '*.c')

DependsOn is also define as part of any given section and should be called in the form of section_type.DependsOn(...)
to allow for better control and faster load times. Existing Depends on calls will in general be the same as calling build.DependsOn(...)

.. code-block:: python

    # faster and preferred
    build.DependsOn([Component("foo")])
    # same as above.. but not has fast to process
    DependsOn([Component("foo")])

    # unit test depends on the build section of another component
    unit_test.DependsOn([Component("foo",section="build")])

One of the advantages of the new section logic is that DependsOn internally will resolve dependencies before processing a given section.
This avoids use of Scons subst engine and provides result that can be printed to the scree to help with debugging better.

There are still more tweaks to come in future drops.
Planned items are to allow phases to reuse packages and sdk for faster builds.

DependsOn requirement passing
-----------------------------

One breaking change is the change of REQ.Value(internal=False) to REQ.Value(internal=True) by default. 
This prevents transitive dependencies from be passed on to dependents by default. 
This will make component more clear on what is required and speed up build by not passing items as LIBS that are not needed.

Given that this can break existing components a COMPAT_REQ_INTERNAL variable can be defined to allow the old behavior. 
This can be define on the CLI or in the SConstruct. It is recommended to apply this to Part that needed it in the Sconstruct.

.. code-block:: python

    Part("foo.part",COMPAT_REQ_INTERNAL=True)

code changes to components that want to export dependent value to its dependencies should be done in a fine grain manner.

.. code-block:: python
    
    # avoid this
    build.DependsOn([
        Component("foo",requires=REQ.DEFAULT(internal=False))
        ])

    # prefer this
    build.DependsOn([
        Component("foo",requires=REQ.DEFAULT|REQ.HEADERS(internal=False))
        ])


The Extern Feature
------------------

The extern feature is a more first class method to allow defining a common build file for cases in which the part files cannot be defined as part of the source repository.
This is common for many c/c++ component that are defined in open source.
The may already have a CMake, Automake or some other build setup and cannot or do not want to add a Parts build file to build with SCons.
This feature allows a common repository to be defined to retrieve build files to be used for build a component from source.
Currently only Part calls that define the top level or root part will process the extern argument.
Calls to subparts will ignore this value.

Example
^^^^^^^

This is an example of a Part call using extern.

.. code-block:: python
  
    Part(
    "brotli",
    "#open_source/brotli.part",
    scm_type=ScmOpenGit(server='github.com', repository="google/brotli", tag="v1.0.9"),
    )

Given the extern git repo existed a part file to define build brotli in this example would look like:

.. code-block:: python

    Import('*')
    PartName("brotli")
    PartVersion(GitVersionFromTag("1.0.0.unknown"))


    @build
    def source(env):
        env.CMake()

General Speed up
----------------

Tests have shown general speed up for be between 10-74% depending on target, size of build, full or incremental builds. 
You speeds may vary, but it is believed that build with many components will benefit more than smaller builds.

