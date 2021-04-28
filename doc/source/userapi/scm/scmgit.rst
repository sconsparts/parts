.. py:function:: ScmGit(repository, server=None, protocol=None, branch=None, tag=None, revision=None, patchfile=None, use_cache=None, **kw):

    Will clone source from the provided location.
    An optional patch file can be provided to be applied after the code 
    is cloned and checked out to the requested tag.
    ScmGit support SCM caching feature to make a local git mirror to be reused between
    different builds on the local box and to reduce bandwidth requirements on clone or 
    update commands.
    

    :param str repository: The repository to use to get the source from the git server
    :param Optional[str] server: The option server to be used. 
            If not provided the value of ``$GIT_SERVER`` will be used.
    :param Optional[bool] protocol: The form of the URL to be used for cloning from 
            the git server. 
            If not provided the value of ``$GIT_PROTOCOL`` will be used. 
            By default this is ``https``
    :param Optional[str] branch: The branch to checkout after clone.
            Defaults to default branch of the server.
            This has been classically the "master" branch.
            Cannot be mixed with tag or revision arguments
    :param Optional[str] tag: The tag to checkout after clone.
            If not provided the default branch value is used
            Cannot be mixed with branch or revision arguments
    :param Optional[str] revision:
            The revision to checkout after clone.
            If not provided the default branch value is used
            Cannot be mixed with branch or tag arguments
    :param Optional[str] patchfile: If provided will point to a diff/patch file to apply
             to the source after the source is cloned and checked out correctly.
             This file must be in the format that git can handle via a ``git am <patchfile>``
    :param Optional[bool] use_cache: Allow for manual control if Parts should use the 
            git mirror cache when cloning.
            If not provided the value of ``$USE_SCM_CACHE`` will be used.
    :param **kw: This value is ignored and provided as a way to help
            with future compatibility.

Examples
--------

Checkout default source from git

    .. code-block:: python

        Part("foo.part",vcs_t=ScmGit(server="git.mycorp.com",repository="group/foo"))

Normally you would checkout a number of components from a location such as github.
In these cases it is useful to set the default server.

    .. code-block:: python
        
        # default server for most of the components
        SetOptionDefault("GIT_SERVER", "github.com")

        Part("foo.part",vcs_t=ScmGit(repository="group/foo"))
        Part("boo.part",vcs_t=ScmGit(repository="group2/boo"))

Checkout a tag from git

    .. code-block:: python
        
        Part(
            "foo.part",
            vcs_t=ScmGit(repository="group/foo", tag='v1.0')
            )


Checkout a branch, while only getting the last five commits.
This can greatly speed up time and save space

    .. code-block:: python
        
        Part(
            "foo.part",
            vcs_t=ScmGit(repository="group/foo", branch='9.0.x'),
            GIT_CLONE_ARGS="--depth=5"
            )

Same as above but do it globally

    .. code-block:: python

        # default server for most of the components
        SetOptionDefault("GIT_CLONE_ARGS", "--depth=5")

        Part(
            "foo.part",
            vcs_t=ScmGit(repository="group/foo", branch='9.0.x'),
            )

.. py:function:: GitVersionFromTag(default, prefix='', regex=None, converter)
.. py:function:: env.GitVersionFromTag(default, prefix='', regex=None, converter)

    Allows the getting the version based on the git tag used to retrieve the code.
    If the current commit is not on a tag or a tag does not match the a version,
    a default value can be provided to retrieve the version.
    The default regular expression used is ``r'\d+\.\d+(?:\.\d+)*'``
    
    :param str default: The version to use if there is no match for the tag.
    :param str prefix: If there is a match, This prefix will be tested for in the result and removed.
    :param str regex: A custom regex string to be used find a match on possible tag values.
    :param lambda converter: A optional function that takes regex group that was matched and a Scons Environment
                             It should return the final version value.
    :return: It will return the version based on the tags found, else default value. 
            If there are more than one tag at this commit that matches, the highest
            sorted value will be returned.
    

Examples
--------

A Part file that would build brotli. 
It retrieves it tries to retrieve the version from the git tag.
If falls back to a special dev version to help make it easy to see
that a modified version is being used.

    .. code:: python

        Import('*')
        PartName("brotli")
        PartVersion(GitVersionFromTag("0.0.0.dev"))

        env.CMake()

.. py:function:: env.GitInfo(checkoutdir=None, patched=False)

    retrieve various information and state about what is cloned on disk.
    Optional arguments allow checking for value in git submodule directory.

    :param Optional[str] checkoutdir: optional path to directory to check
    :param bool patched: If set to True, the previous commit will be checked.
    :return: A dictionary with value for these keys

            * branch
            * tags
            * modified
            * untracked
            * server
            * revision
            * short_revision
    

Variables
---------

ScmGit can be control via a number of variables.

.. py:data:: SCM_GIT_CACHE_DIR

    Path to use for the git mirror cache

.. py:data:: GIT_SERVER

    The default git server to use. 
    Defaults to empty string and should be provided by the user.

.. py:data:: VCS_GIT_DIR

    The location where git will clone source to. 
    Defaults to ``${CHECK_OUT_ROOT}/${PART_ALIAS}``

.. py:data:: GIT_DEFAULT_BRANCH

    The default branch to use when checking out a branch
    Defaults to ``master``

.. py:data:: GIT_IGNORE_UNTRACKED

    Tell Parts when doing update check to ignore untracked files from being viewed
    as being a difference. normally these files would be defined in the .gitignore 
    file. 
    It is common however that files may not have been added for various reasons
    Defaults to False

.. py:data:: SCM_IGNORE_MODIFIED

    General value that when set will allow git to ignore modified files when 
    doing updates.
    Useful for cases when build a component has side effects of modifying sources.
    Normally these files should not have been checked in, 
    however for various reason this can happen when building and calling scripts 
    or third-party build systems.

.. py:data:: GIT_PROTOCOL

    Support to clone via two different protocols is supported.
    
    **https** (default)
        which is in the form of `https://<server>/<repository>.git`

        **example**  `https://bitbucket.org/sconsparts/parts.git`

    **ssh**
        which is the form of `git@<server>:<repository>.git`
        
        **example** `git@bitbucket.org:sconsparts/parts.git`

    In both cases the ".git" will be added if not provided with the repository argument 

.. py:data:: GIT_TAG_ARGS
    
    Optional extra arguments when Parts tries to query for ``git tag``.

.. py:data:: GIT_STATUS_ARGS

    Optional extra arguments when Parts tries to query for ``git status``.

.. py:data:: GIT_CLONE_ARGS

    Optional extra arguments when Parts goes a ``git clone``.

.. py:data:: GIT_CHECKOUT_ARGS

    Optional extra arguments when Parts goes a ``git checkout``.

.. py:data:: GIT_AM_ARGS

    Optional extra arguments when Parts goes a ``git as`` as part of patching the source.
.. py:data:: GIT_FETCH_ARGS

    Optional extra arguments when Parts goes a ``git fetch``.
.. py:data:: GIT_PULL_ARGS

    Optional extra arguments when Parts goes a ``git pull``.
.. py:data:: GIT_RESET_ARGS

    Optional extra arguments when Parts goes a ``git reset``.

