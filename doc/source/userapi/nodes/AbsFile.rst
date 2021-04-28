.. py:function:: AbsFileNode(path)
.. py:function:: env.AbsFileNode(path)

    Creates a node that are outside the current parts file directory.
    By default SCons does not like referring to files outside the current directory tree 
    that contains the SConscript, SConstruct or Parts file. 
    Part of the reason is how SCons deals with variant directories.
    This function allow for referring to these files by mapping the node correctly to 
    one of two specially made variant directories. 
    One of these directories is for files under the current SConstruct directory but
    outside the directory of the defining Parts file
    referred to via the $ROOT_BUILD_DIR variable.
    The other is for file out the the current SConstruct directory tree, 
    referred to via the $OUTOFTREE_BUILD_DIR variable.
    
    .. note::

        Note calling this function may still allow the file to build, however 
        the file will build in the source tree not in the build/variant directory tree.
        This can lead to bad built states in case of cross builds that can add to build
        time or bad build states, beside messing up the source tree with unneeded files.


    :param str path: path to file
    :return: SCons File node to the file.

Examples
--------

Copy a header file to the SDK directory to be used by other components

.. code-block:: python

    env.SdkInclude([
        AbsFileNode('../include/optional.h')]
        )

Build source that is not under the part file. 
This is often useful if the user like to have a `build` directory with all the build files

.. code-block:: python

    env.Program([
        AbsFileNode('../src/main.c')
        ])


Same as the above but for a case in which the build files are not part of the source
code repository.

.. code-block:: python

    env.Program([
        AbsFileNode('${CHECK_OUT_DIR}/src/main.c')
        ])

.. py:function:: AbsFile(path)
.. py:function:: env.AbsFile(path)

    This is the same as :func:`AbsFileNode`, except it returns a string. 
    Prefer to calling :func:`AbsFileNode` this function.
    However there are cases in which the path to the source file may be needed
    as a string.

    It is equivalent to calling

    .. code-block:: python
        
        AbsFileNode("../some/path").srcnode().abspath

