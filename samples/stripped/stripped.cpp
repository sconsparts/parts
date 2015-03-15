#include <iostream>

using namespace std;

int main(int argc, char** argv)
{
    cout << argv[0] << " executed with ";
    if (argc > 1)
    {
        cout << "the following arguments:";
        int i;
        for (i = 1; i < argc; ++i)
        {
            cout << " " << argv[i];
        }
    }
    else
    {
        cout << "no arguments";
    }

    cout << endl;

    return 0;
}

