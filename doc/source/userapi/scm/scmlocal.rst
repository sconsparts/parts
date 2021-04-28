.. py:function:: ScmLocal(path)

    This allow referring to a component on the local disk.
    Does not copy any source. 
    The default SCM object if one was not defined by the Part() call.

    :param str path: The location to directory containing the Parts file.

Examples:
---------

These two Part call are equivalent.

    .. code:: python
    
        Part('core.part',vcs_type=ScmLocal('./src'))
        Part('src/core.part')



