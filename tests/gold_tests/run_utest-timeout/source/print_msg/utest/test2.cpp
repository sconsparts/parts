#include <iostream>

#ifdef _WINDOWS
#include <windows.h>
#else
#include <unistd.h>
#define Sleep(x) usleep((x)*1000)
#endif

#include <stdio.h>
#define PRINT_MSG printf("hello world from print_msg()")

int main()
{
    PRINT_MSG;
    Sleep(15 * 1000);
    std::cout<<"; test #2 passed"<<std::endl;
    return 0;
}
