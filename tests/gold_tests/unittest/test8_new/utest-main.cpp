#include <sys/types.h>
#include <sys/stat.h>

int main(int argc, char** argv)
{
    struct stat buf = {0};

    if (stat("datafile.txt", &buf) == 0)
    {
        return 1;
    }
    return 2;
}

