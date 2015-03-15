This example demonstrates WiX preprocessor variables usage.

The preprocessor supports three types of variables:

1. $(sys.VariableName) system variable. WiX 3.5.1 has the following system variables:
    CURRENTDIR - the candle.exe process current working directory.
    SOURCEFILEPATH - full path to the source file being processed.
    SOURCEFILEDIR - path to a directory where currently being processed source file is located.
    PLATFORM has either Intel, x64, or Intel64 value

2. $(env.VariableName) system environment variable.

3. $(var.VariableName) - variable either defined with <?define ?> directive or passed with -d command line switch.