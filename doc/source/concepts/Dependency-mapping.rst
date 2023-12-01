Dependency mapping
------------------

Parts adds the ability to map dependencies between different parts.
This allow for the ability to implicitly or explicitly map paths and 
other values needed to build dependent components.
This is done via the DependsOn() function and Component() objects that define the matching 
and options property requirements of the dependent Part.
Match of a dependance is done via finding a unique "best match" based on values provided by the user.
If a ambiguous match or no match based on provided requirements, such as the requested version range,
are found the build system will error out reporting all requirements could not be found.
This allows for a more agile build system, increases productivity and confidence in the build, 
especially for larger "mega" projects.
