
#include <string>

#ifdef WINDOW_OS
# ifdef COMMON_EXPORTS
#	define COMMON_API __declspec(dllexport)
# else
#	define COMMON_API __declspec(dllimport)
# endif
#else
#	define COMMON_API
#endif

COMMON_API void common(std::string const& str);