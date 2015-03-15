
#include <stdlib.h>
#include <stdio.h>


int main(int argc, char ** argv)
{
	char* var = getenv( "FOO_VAR" );
	if( var == NULL ){
		/*variable was not found*/
		return 1;
	}

	return 0;
}
