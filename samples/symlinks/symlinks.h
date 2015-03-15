#ifndef __SYMLINKS_H__
#define __SYMLINKS_H__

#if defined(__linux__) || defined(__APPLE__)
#define SYMLINKS_API
#else
#define SYMLINKS_API __declspec(dllexport)
#endif

#endif // __SYMLINKS_H__

