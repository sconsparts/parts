.. py:function:: PartName(name=None)

    Defines the name of the given Part.
    If name is not provided, the function will return the current defined name of the Part. 
    If name is not explicitly set Parts will fallback to the name of Part file without the file extension will be used

    :param str name: the name of this Part. 
    :return: Full name of the Part.
    :rtype: str


Examples
--------

Set the Name of the Part to "core"

.. code-block:: python

   PartName("core")

Get the current name and print the value.

.. code-block:: python

    name = PartName()
    print("Current PartName is:" name)

A note on this example. 
=======================
If this is top level part the value return would match what it was set to. 
If it was a subpart the value will be set to the value of the parent part plus the value of this part separated by a '.'
Given we set the name to "core" as in the first example, PartName would return:
 * **core** if this was a top level part
 * **parent**.core** if this was a subpart.