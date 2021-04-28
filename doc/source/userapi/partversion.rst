.. py:function:: PartVersion(ver=None)

    Defines the Version of the given Part.
    The version can only be defined once with in a given Part/sub-part structure,
    because of this it is recommended to define the version at the top level.
    If the version is defined twice the first call will win and and remaining calls
    will result in a warning message
    If version is not provided, the function will return the current defined name of the Part. 
    If name is not explicitly set Parts will fallback to the a version of 0.0.0

    :param Optional[str|Version] name: The version of this Part.
    :return: Version of the Parts.
    :rtype: str

Examples
--------

Set the version

.. code-block:: python

   PartVersion("2.0.3")

.. code-block:: python

   PartVersion(Version("2.0.3"))
