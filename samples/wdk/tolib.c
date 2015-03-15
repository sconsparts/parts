extern int static_library_function(int argument);

__declspec(dllexport)int
library_function(int argument)
{
    return static_library_function(argument);
}

