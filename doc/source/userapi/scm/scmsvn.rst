.. py:function:: ScmSvn(repository, server=None, revision=None)

    Retrieves source from SVN based on provided information

    :param str repository: The repository or path from server under the server to get our data from
    :param Optional[str] server: The server to connect to
    :param Optional[str] revision: The optional revision to get. Defaults to latest revision

.. py:function:: SvnInfo(checkoutdir=None)

    Retrieves svn information about source on disk.    

    :param Optional[str] checkoutdir: optional alternate directory to try to retrieve information from
    :return: returns a dictionary with values to these keys:
        
        * revision
        * revision_low
        * modified
        * switched
        * partial
        * url
        * server

Variables
---------

ScmSvn can be control via a number of variables.

.. py:data:: SVN_SERVER

    The svn server to use by default

.. py:data:: SVN_FLAGS

    A list of of optional flags to add to any SVN command. 
    By default ``['--non-interactive']``

.. py:data:: VCS_SVN_DIR

    The location where SVN will checked out the source to.
    Defaults to ``${CHECK_OUT_ROOT}/${PART_ALIAS}``
