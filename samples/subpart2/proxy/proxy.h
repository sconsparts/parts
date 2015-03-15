

#ifdef WINDOW_OS
# ifdef PROXY_EXPORTS
#	define PROXY_API __declspec(dllexport)
# else
#	define PROXY_API __declspec(dllimport)
# endif
#else
#	define PROXY_API
#endif

PROXY_API void proxy();
