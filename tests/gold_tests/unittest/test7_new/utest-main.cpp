#include <sys/types.h>
#include <sys/stat.h>

#ifdef WIN32
#define EXENAME "main.exe"
#else
#define EXENAME "main"
#endif

int main(int argc, char** argv)
{
    struct stat buf = {0};

    if (stat(EXENAME, &buf) == 0)
    {
        return 1;
    }

    return 2;
}

