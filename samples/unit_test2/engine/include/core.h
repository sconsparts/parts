
#ifdef WINDOW_OS
# ifdef CORE_EXPORTS
#	define CORE_API __declspec(dllexport)
# else
#	define CORE_API __declspec(dllimport)
# endif
#else
#	define CORE_API
#endif

extern CORE_API void core();