
#ifdef WINDOW_OS
# ifdef OPTIONAL_EXPORTS
#	define OPTIONAL_API __declspec(dllexport)
# else
#	define OPTIONAL_API __declspec(dllimport)
# endif
#else
#	define OPTIONAL_API
#endif

OPTIONAL_API void optional();