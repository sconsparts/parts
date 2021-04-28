.. py:function:: ScmReuse(part)

    Allow the reuse of a previously checkout/clone Part.
    This avoid wasting disk space for cases in which the repository 
    has more than one component defined in it.

    :param Union[str,Part object] part: The Part Alias to use reuse or the Part object
        returned from calling the Part() function

Examples:
---------

Build Part A and B from the same repository, via using an alias

    .. code:: python

        Part("a","a.part",vcs_type=ScmGit("myprojects/proj_a"))
        Part("a","a.part",vcs_type=ScmReuse("a"))

The same as above but via passing an object

    .. code:: python

        a_part = Part("a","a.part",vcs_type=ScmGit("myprojects/proj_a"))
        Part("a","a.part",vcs_type=ScmReuse(a_part))