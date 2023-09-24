#include "stdio.h"
void __analyzer_eval(int);
int *f(int *);

int *f(int *q)
{
    __analyzer_eval(q == 0);
    if (q == 0)
    {
        __analyzer_eval(q == 0);
        if (*q == 0)
        {
            printf("Hello World!");
        }
    }
}