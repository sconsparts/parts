.. py:function:: AbsDirNode(path)
.. py:function:: env.AbsDirNode(path)

    Creates a node that are outside the current parts file directory.
    By default SCons does not like referring to directories outside the current directory tree 
    that contains the SConscript, SConstruct or Parts file. 
    Part of the reason is how SCons deals with variant directories.
    This function allow for referring to these files by mapping the node correctly to 
    one of two specially made variant directories. 
    One of these directories is for directories under the current SConstruct directory but
    outside the directory of the defining Parts file
    referred to via the $ROOT_BUILD_DIR variable.
    The other is for directories out the the current SConstruct directory tree, 
    referred to via the $OUTOFTREE_BUILD_DIR variable.

    :param str path: path to directory
    :return: SCons directory node to the directory

Examples
--------

Add directory to path that is outside the current tree

.. code-block:: python

    env.Append(CPPPATH= [env.AbsDirNode('../include')])


.. py:function:: AbsDir(path)
.. py:function:: env.AbsDir(path)

    This is the same as :func:`AbsDirNode`, except it returns a string. 
    Prefer to calling :func:`AbsDirNode` this function.
    However there are cases in which the path to the source file may be needed
    as a string.

    It is equivalent to calling

    .. code-block:: python
        
        AbsDirNode("../some/path").srcnode().abspath