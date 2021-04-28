Mappers
-------

The SCons substitution engine provides a way for user to define a callable object.
Mappers formalize this ability to define objects to make it easier to extend and add 
new functions to be used for substitution. 
One feature of the Mappers object is the ability to control if the value should be 
cached, which can greatly speed up the over all build time.
Parts uses a set of Mappers to help communicate values between different components.
