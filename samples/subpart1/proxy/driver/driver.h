
//print_msg.h
#ifdef WINDOW_OS
# ifdef DRIVER_EXPORTS
#	define DRIVER_API __declspec(dllexport)
# else
#	define DRIVER_API __declspec(dllimport)
# endif
#else
#	define DRIVER_API
#endif
DRIVER_API void driver();
