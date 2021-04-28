.. py:function:: env.Sdk(source, sub_dir='', add_to_path=True, auto_add_libs=True, use_src_dir=False, create_sdk=True)
.. py:function:: env.SdkTarget(source, sub_dir='', add_to_path=True, auto_add_libs=True, use_src_dir=False, create_sdk=True)

    Copies the sources to the SDK lib or bin directory based on the extension of the file.
    Files that match the SDK_LIB_PATTERN will be copied to the $SDK_LIB locations
    File that match the SDK_BIN_PATTERN will be copied to the $SDK_BIN locations. 
    On POSIX based system, if the file has no extension and did not match the above pattern 
    the file will copied as a binary file.

    

    