.. py:function:: Pattern(src_dir='./', includes=['*'], excludes=[], recursive=True)
.. py:function:: env.Pattern(src_dir='./', includes=['*'], excludes=[], recursive=True)

    This is like the SCons Glob function, but returns a Pattern object.
    It allow for searching for a pattern of files while providing a clear means to
    to include or exclude certain patterns of files.
    The main difference is that the Pattern object form the Glob object is that the 
    Pattern object makes it easy to exclude patterns, and do recursive searches, 
    whereas the Glob() does not.
    Various copy based functions provided by Parts accept Pattern objects to allow 
    preserving the structure of the nodes, whereas node passed in from Glob would lose
    this structure and be flatten to same location.
    The current input patterns for including or excluding file are in the table below
    and are based on python fnmatch library.

    =========   ================================
    Pattern     Meaning 
    =========   ================================
    \*           Matches everything
    ?           Matches any single character
    [seq]       Matches any character in seq
    [!seq]      Matches any character not in seq
    =========   ================================

    :param str sub_dir: deprecated and currently ignored
    :param str src_dir: optional directory used as the root for were the search for files should start
    :param List[str] includes: optional list of pattern to use for finding a match
    :param List[str] excludes: optional list of patterns to exclude if the file did match one of the includes patterns
    :rtype: Pattern

    
.. class:: Pattern

    .. method:: files(directory=None)

        Useful when giving the files to native SCons functions that don’t understand Pattern
        object as a first class object.

        :param str directory: Allow selection of files at the given directory level. 
                            If None is given all files are provided
        :returns: Returns list of file nodes that match the pattern.


    .. method:: sub_dirs()

        Returns a lists of all the subdirectories that are known by the pattern

        :returns: List of directory nodes

    .. method:: target_source(root_target):

        Useful when implementing a builder or calling a build in which directory structure
        should not be lost.

        :arg str root_target: The root directory to bind all source nodes to.

Examples
--------

Scan for C and CPP file to build as Program()

.. code-block:: python

   files = Pattern(includes=['*.cpp','*.c']).files()
   env.Program("myapp",files)

Copy all headers to the be installed, but skip file in 'private' directory.
the directory structure under include directory will be preserved. 

.. code-block:: python

   env.InstallInclude(
        Pattern(src_dir="include",includes="*.h",excludes="private/*")
    )

Verbose Tags
------------

**pattern.add**
    Prints item that are add as a match during the scan

**pattern.skip**
    Prints item that are skipped during the scan

