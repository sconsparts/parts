Components/Parts
----------------

One of the core concepts Parts adds to SCons is the notion of a component referred to as a Part.
A Part is defined by a file ending via `.part` or `.parts` that is loaded via a call to the Part() function.
The extension is a convention and is not enforced.
A given Part may define other Parts that are referred to as a sub-Part. 
A Part defines a set of given properties that can be defined by the user such as:

* Alias
* Name
* Version
* Various import values
* Various export values

These values allow for the easy plugin and play like consumption of an existing component into a different Scons build that uses Parts.

Sub-Parts
---------
A Part can be defined as a sub-component of another Part. 
The sub-Parts can not define a version, which can only be defined by the top-level 
Part and they extend the provided name in the form of:

**<Parts name>.<sub-part name>`**

See the Part Name section for more details on how names are constructed and handled.

There is no limit to how many sub-groupings are defined for a given Parts or 
how deep the level of sub-part defined.
In general, one should only define sub-part to help define structure in the 
component to help with the definition of build targets or values to be exported 
and shared with other components