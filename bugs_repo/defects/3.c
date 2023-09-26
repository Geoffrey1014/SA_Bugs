#include "stdio.h"
void __analyzer_eval();
void __analyzer_dump();

void main()
{
    int *b[1] = {};
    int **c = &b[0];
    if (c == &b[0])
    {
        __analyzer_dump();
        int *p = (int *)0;
        __analyzer_describe(1, c+1);
        __analyzer_describe(1, (&b[0]) + 1);
        __analyzer_eval((((c) + 1) == ((&b[0]) + 1)));
        if (((c) + 1) == ((&b[0]) + 1))
        {
            *p = 42;
        }
    }
}
