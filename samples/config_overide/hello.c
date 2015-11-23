#include <stdio.h>
int main()
{
// so our custom value was added to the build configuration
#ifndef THIS_IS_A_CUSTOM_VALUE
#error Expected to have THIS_IS_A_CUSTOM_VALUE defined
#endif
	printf("hello world");
	return 0;
}