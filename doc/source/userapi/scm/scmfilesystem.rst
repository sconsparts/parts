.. py:function:: ScmFileSystem(repository, server=None)

    Allow retrieval of source from a file system mount.
    Supports Windows UNC path formats, i.e. ``\\<ServerName>\<RepositoryPath>``
    
    :param str repository: The path under the server or mount point to use
    :param Optional[str] server: The server or mount point to use.


Examples:
---------

Get sources from internal location

    .. code:: python

        if use_unc_path:
            SetOptionDefault('FILE_SYSTEM_SERVER','\\code.server')
        else:
            SetOptionDefault('FILE_SYSTEM_SERVER','/mnt/code')

        Part("compA.part",vcs_type=ScmFileSystem("components/mycompA))

Variables
---------

ScmFileSystem can be control via a number of variables.

.. py:data:: FILE_SYSTEM_SERVER

    The file server to use.

.. py:data:: VCS_FILESYSTEM_DIR

    The location where files will be copy the source to.
    Defaults to ``${CHECK_OUT_ROOT}/${PART_ALIAS}``


